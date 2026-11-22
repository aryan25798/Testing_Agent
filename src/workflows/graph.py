"""
LangGraph Testing Workflow Graph.
Orchestrates the 6 specialized AI testing agents as a state machine.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.workflows.state import TestingWorkflowState
from src.agents.requirement_analysis.agent import RequirementAnalysisAgent, RequirementAnalysisInput
from src.agents.scenario_generation.agent import ScenarioGenerationAgent, ScenarioGenerationInput, GeneratedScenario
from src.agents.test_case_design.agent import TestCaseDesignAgent, TestCaseDesignInput, GeneratedTestCase
from src.agents.test_automation.agent import TestAutomationAgent, AutomationGenerationInput
from src.agents.test_execution.agent import TestExecutionAgent, ExecutionTarget
from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent
from src.database.session import SessionLocal
from src.models.entities import (
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
)
from src.core.logging import get_logger

logger = get_logger("workflow_graph")

# Initialize Agent Instances
req_agent = RequirementAnalysisAgent()
scen_agent = ScenarioGenerationAgent()
tc_agent = TestCaseDesignAgent()
auto_agent = TestAutomationAgent()
exec_agent = TestExecutionAgent()
report_agent = OrchestrationReportingAgent()


# --- Node Definitions ---

def requirement_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 1: Requirement Analysis...")
    raw_text = state["raw_input_text"]
    source_type = state.get("source_type", "manual")

    if state.get("project_id"):
        parts = []
        try:
            import asyncio
            from src.integrations.mcp.mcp_agent_client import mcp_agent_client
            git_data = asyncio.run(mcp_agent_client.get_github_file(state["project_id"], "README.md"))
            if git_data:
                parts.append(f"GITHUB SPECIFICATION (VIA GITHUB MCP):\n{git_data}")
        except Exception as e:
            logger.warning(f"Could not fetch from GitHub MCP: {e}")

        # Deterministic AST Code Indexer (Zero-cost contract extraction for massive monorepos)
        try:
            from src.integrations.git.ast_indexer import ast_code_indexer
            contract_summary = ast_code_indexer.index_directory(".")
            if contract_summary.frontend_routes or contract_summary.api_endpoints:
                compact_contract = contract_summary.to_compact_markdown()
                parts.append(f"STATIC CODE AST CONTRACT (DETERMINISTIC ZERO-COST SLICER):\n{compact_contract}")
        except Exception as e:
            logger.warning(f"Could not index static code interface contracts: {e}")

        try:
            import asyncio
            from src.integrations.mcp.mcp_agent_client import mcp_agent_client
            jira_data = asyncio.run(mcp_agent_client.get_jira_issues(state["project_id"]))
            if jira_data:
                jira_str = "\n".join([str(item.get("raw_content")) for item in jira_data])
                parts.append(f"JIRA USER STORIES (VIA ATLASSIAN MCP):\n{jira_str}")
        except Exception as e:
            logger.warning(f"Could not fetch from Jira MCP: {e}")

        if parts:
            combined = "\n\n---\n\n".join(parts)
            if state.get("raw_input_text"):
                raw_text = f"{combined}\n\nTARGET APPLICATION AUTHENTICATION & ENVIRONMENT:\n{state['raw_input_text']}"
            else:
                raw_text = combined

    inp = RequirementAnalysisInput(
        raw_text=raw_text,
        title="Project Requirements",
        source_type=source_type,
    )
    result = req_agent.run(inp, project_id=state["project_id"])
    reqs_dicts = [r.model_dump() for r in result.requirements]

    # Save to database
    with SessionLocal() as db:
        for r in result.requirements:
            existing = db.query(Requirement).filter(
                Requirement.project_id == state["project_id"],
                Requirement.requirement_key == r.requirement_key,
            ).first()
            if not existing:
                db_req = Requirement(
                    project_id=state["project_id"],
                    requirement_key=r.requirement_key,
                    source_type=state.get("source_type", "manual"),
                    title=r.title,
                    description=r.description,
                    business_objective=r.business_objective,
                    functional_requirements=r.functional_requirements,
                    non_functional_requirements=r.non_functional_requirements,
                    acceptance_criteria=r.acceptance_criteria,
                    business_rules=r.business_rules,
                    dependencies=r.dependencies,
                    missing_information=r.missing_information,
                    clarification_questions=r.clarification_questions,
                    risk_level=r.risk_level,
                    priority=r.priority,
                    testability_status=r.testability_status,
                    is_approved=True,  # Approved for pipeline flow
                )
                db.add(db_req)
        db.commit()

    return {
        "requirements": reqs_dicts,
        "approved_requirements": reqs_dicts,
        "current_agent": "agent_1_requirement_analysis",
        "step_count": state.get("step_count", 0) + 1,
    }


def scenario_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 2: Test Scenario Generation...")
    # Map dicts to ExtractedRequirement
    from src.agents.requirement_analysis.agent import ExtractedRequirement
    req_objs = [ExtractedRequirement.model_validate(r) for r in state["approved_requirements"]]
    inp = ScenarioGenerationInput(requirements=req_objs)
    result = scen_agent.run(inp, project_id=state["project_id"])
    scen_dicts = [s.model_dump() for s in result.scenarios]

    # Save to database
    with SessionLocal() as db:
        for s in result.scenarios:
            req_record = db.query(Requirement).filter(
                Requirement.project_id == state["project_id"],
                Requirement.requirement_key == s.requirement_key,
            ).first()
            req_id = req_record.id if req_record else state["project_id"]

            existing = db.query(TestScenario).filter(
                TestScenario.project_id == state["project_id"],
                TestScenario.scenario_key == s.scenario_key,
            ).first()
            if not existing:
                db_scen = TestScenario(
                    project_id=state["project_id"],
                    requirement_id=req_id,
                    scenario_key=s.scenario_key,
                    title=s.title,
                    description=s.description,
                    test_type=s.test_type,
                    preconditions=s.preconditions,
                    test_objective=s.test_objective,
                    priority=s.priority,
                    risk=s.risk,
                    expected_outcome=s.expected_outcome,
                    automation_suitability=s.automation_suitability,
                    is_approved=True,
                )
                db.add(db_scen)
        db.commit()

    return {
        "test_scenarios": scen_dicts,
        "approved_scenarios": scen_dicts,
        "current_agent": "agent_2_scenario_generation",
        "step_count": state["step_count"] + 1,
    }


def test_case_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 3: Test Case Design...")
    scen_objs = [GeneratedScenario.model_validate(s) for s in state["approved_scenarios"]]
    inp = TestCaseDesignInput(scenarios=scen_objs)
    result = tc_agent.run(inp, project_id=state["project_id"])
    tc_dicts = [tc.model_dump() for tc in result.test_cases]

    # Save to database
    with SessionLocal() as db:
        for tc in result.test_cases:
            scen_record = db.query(TestScenario).filter(
                TestScenario.project_id == state["project_id"],
                TestScenario.scenario_key == tc.scenario_key,
            ).first()
            scen_id = scen_record.id if scen_record else state["project_id"]
            req_id = scen_record.requirement_id if scen_record else state["project_id"]

            existing = db.query(TestCase).filter(
                TestCase.project_id == state["project_id"],
                TestCase.test_case_key == tc.test_case_key,
            ).first()
            if not existing:
                db_tc = TestCase(
                    project_id=state["project_id"],
                    scenario_id=scen_id,
                    requirement_id=req_id,
                    test_case_key=tc.test_case_key,
                    title=tc.title,
                    objective=tc.objective,
                    test_type=tc.test_type,
                    priority=tc.priority,
                    preconditions=tc.preconditions,
                    test_environment=tc.test_environment,
                    test_data=tc.test_data,
                    execution_steps=[step.model_dump() for step in tc.execution_steps],
                    expected_results=tc.expected_results,
                    status="Approved",
                    automation_suitability=tc.automation_suitability,
                    tags=tc.tags,
                    is_approved=True,
                )
                db.add(db_tc)
        db.commit()

    return {
        "test_cases": tc_dicts,
        "approved_test_cases": tc_dicts,
        "current_agent": "agent_3_test_case_design",
        "step_count": state["step_count"] + 1,
    }


def automation_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 4: Test Automation Generation...")
    tc_objs = [GeneratedTestCase.model_validate(tc) for tc in state["approved_test_cases"]]
    inp = AutomationGenerationInput(
        test_cases=tc_objs,
        framework=state.get("framework", "playwright"),
        browser_name=state.get("browser", "chromium") or "chromium",
        base_url=state.get("base_url", "http://127.0.0.1:8000"),
    )
    result = auto_agent.run(inp, project_id=state["project_id"])
    scripts_dicts = [s.model_dump() for s in result.scripts]

    # Save to database
    with SessionLocal() as db:
        for s in result.scripts:
            existing = db.query(AutomationScript).filter(
                AutomationScript.project_id == state["project_id"],
                AutomationScript.script_name == s.script_name,
            ).first()
            if not existing:
                db_script = AutomationScript(
                    project_id=state["project_id"],
                    framework=s.framework,
                    script_name=s.script_name,
                    file_path=s.file_path,
                    code_content=s.code_content,
                    syntax_valid=s.syntax_valid,
                    is_approved=True,
                )
                db.add(db_script)
        db.commit()

    return {
        "automation_scripts": scripts_dicts,
        "current_agent": "agent_4_test_automation",
        "step_count": state["step_count"] + 1,
    }


def execution_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 5: Test Execution & Validation...")
    targets = []
    for s in state["automation_scripts"]:
        if s["script_name"].startswith("test_"):
            targets.append(
                ExecutionTarget(
                    test_case_key=s.get("test_case_key") or "TC-001",
                    title=f"Automated Run - {s['script_name']}",
                    script_path=s["file_path"],
                    code_content=s["code_content"],
                )
            )

    report = exec_agent.run(
        targets=targets,
        runner_type=state.get("framework", "playwright"),
        base_url=state.get("base_url", "http://127.0.0.1:8000"),
        browser=state.get("browser", "chromium") or "chromium",
        project_id=state["project_id"],
    )

    return {
        "execution_results": [r.model_dump() for r in report.results],
        "current_agent": "agent_5_test_execution",
        "step_count": state["step_count"] + 1,
    }


def reporting_node(state: TestingWorkflowState) -> Dict[str, Any]:
    logger.info("Executing Agent 6: Test Orchestration & Reporting...")
    report = report_agent.generate_consolidated_report(project_id=state["project_id"])
    return {
        "consolidated_report": report.model_dump(),
        "workflow_status": "Completed",
        "current_agent": "agent_6_orchestration_reporting",
        "step_count": state["step_count"] + 1,
    }


# Build LangGraph StateGraph
def build_testing_graph():
    builder = StateGraph(TestingWorkflowState)

    builder.add_node("requirement_analysis", requirement_node)
    builder.add_node("scenario_generation", scenario_node)
    builder.add_node("test_case_design", test_case_node)
    builder.add_node("test_automation", automation_node)
    builder.add_node("test_execution", execution_node)
    builder.add_node("orchestration_reporting", reporting_node)

    builder.set_entry_point("requirement_analysis")
    builder.add_edge("requirement_analysis", "scenario_generation")
    builder.add_edge("scenario_generation", "test_case_design")
    builder.add_edge("test_case_design", "test_automation")
    builder.add_edge("test_automation", "test_execution")
    builder.add_edge("test_execution", "orchestration_reporting")
    builder.add_edge("orchestration_reporting", END)

    return builder.compile()


testing_graph = build_testing_graph()
