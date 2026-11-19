"""
Unit Tests for the Six Specialized Testing Agents.
"""

import pytest
from src.agents.requirement_analysis.agent import RequirementAnalysisAgent, RequirementAnalysisInput
from src.agents.scenario_generation.agent import ScenarioGenerationAgent, ScenarioGenerationInput, ExtractedRequirement
from src.agents.test_case_design.agent import TestCaseDesignAgent, TestCaseDesignInput, GeneratedScenario
from src.agents.test_automation.agent import TestAutomationAgent, AutomationGenerationInput, GeneratedTestCase
from src.agents.test_execution.agent import TestExecutionAgent, ExecutionTarget
from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent
from src.database.session import SessionLocal
from src.models.entities import Project


def test_agent_1_requirement_analysis():
    agent = RequirementAnalysisAgent()
    inp = RequirementAnalysisInput(
        raw_text="The system must allow users to log in with an email and password. Passwords must be at least 8 characters. After 3 failed attempts, the account should be locked.",
        source_type="manual",
    )
    result = agent.run(inp)

    assert len(result.requirements) > 0
    req = result.requirements[0]
    assert req.title != ""
    assert len(req.acceptance_criteria) > 0
    assert req.risk_level in ["Low", "Medium", "High", "Critical"]
    assert req.testability_status in ["Testable", "Needs Clarification", "Untestable"]


def test_agent_2_scenario_generation():
    agent = ScenarioGenerationAgent()
    req = ExtractedRequirement(
        requirement_key="REQ-001",
        title="User Authentication",
        description="Users must authenticate with email and password.",
        business_objective="Secure user access to personal accounts.",
        functional_requirements=["Validate email format", "Authenticate password hash"],
        acceptance_criteria=["Valid login redirects to dashboard", "Invalid password shows error"],
        business_rules=["Max 3 failed attempts"],
        risk_level="High",
        priority="High",
    )
    result = agent.run(ScenarioGenerationInput(requirements=[req]))

    assert len(result.scenarios) >= 4
    test_types = {s.test_type for s in result.scenarios}
    assert "Positive" in test_types
    assert "Negative" in test_types
    for s in result.scenarios:
        assert s.requirement_key == "REQ-001"


def test_agent_3_test_case_design():
    agent = TestCaseDesignAgent()
    scen = GeneratedScenario(
        scenario_key="SCEN-001",
        requirement_key="REQ-001",
        title="Verify Positive Authentication",
        description="User supplies registered email and matching password.",
        test_type="Positive",
        preconditions="User account exists and is active.",
        test_objective="Confirm happy path login redirects to dashboard.",
        expected_outcome="User lands on dashboard with valid session token.",
    )
    result = agent.run(TestCaseDesignInput(scenarios=[scen]))

    assert len(result.test_cases) > 0
    tc = result.test_cases[0]
    assert tc.scenario_key == "SCEN-001"
    assert len(tc.execution_steps) > 0
    assert "step_number" in tc.execution_steps[0].model_dump()
    assert tc.test_data != {}


def test_agent_4_test_automation_playwright():
    agent = TestAutomationAgent()
    tc = GeneratedTestCase(
        test_case_key="TC-001",
        scenario_key="SCEN-001",
        requirement_key="REQ-001",
        title="Login Happy Path",
        objective="Verify login succeeds",
        preconditions="User is registered",
        test_data={"user": "test@example.com"},
        execution_steps=[],
        expected_results="Dashboard displayed",
    )
    result = agent.run(AutomationGenerationInput(test_cases=[tc], framework="playwright"))

    assert len(result.scripts) >= 3  # conftest, base_page, test_tc_001
    assert result.framework == "playwright"
    for s in result.scripts:
        assert s.syntax_valid is True, f"Syntax error in {s.file_path}: {s.validation_error}"


def test_agent_4_test_automation_selenium():
    agent = TestAutomationAgent()
    tc = GeneratedTestCase(
        test_case_key="TC-002",
        scenario_key="SCEN-001",
        requirement_key="REQ-001",
        title="Selenium Login Test",
        objective="Verify login via Selenium",
        preconditions="Driver available",
        test_data={"user": "test@example.com"},
        execution_steps=[],
        expected_results="Success",
    )
    result = agent.run(AutomationGenerationInput(test_cases=[tc], framework="selenium"))

    assert len(result.scripts) >= 3
    assert result.framework == "selenium"
    for s in result.scripts:
        assert s.syntax_valid is True


def test_agent_5_test_execution_sandbox():
    agent = TestExecutionAgent()
    target = ExecutionTarget(
        test_case_key="TC-001",
        title="Verification Test",
        script_path="tests/test_dummy.py",
        code_content="def test_sanity(): assert 1 + 1 == 2",
    )
    report = agent.run(targets=[target])
    assert report.total_tests == 1
    assert report.passed_tests == 1
    assert report.failed_tests == 0


def test_agent_6_reporting_metrics():
    # Create temporary project in DB
    with SessionLocal() as db:
        p = Project(name="Metrics Verification Project", framework="playwright")
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

    agent = OrchestrationReportingAgent()
    report = agent.generate_consolidated_report(project_id=pid)
    assert report.project_name == "Metrics Verification Project"
    assert report.requirement_coverage_pct >= 0.0
    assert report.automation_coverage_pct >= 0.0
    assert "Executive Summary" in report.markdown_report
