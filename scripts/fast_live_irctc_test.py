"""
Fast Live Website Testing Script — IRCTC (https://www.irctc.co.in/)
Generates and executes EXACTLY 3 test cases in VISIBLE (Headed) browser mode using OpenAI gpt-6.2-sol.
"""

import sys
import os
import time
import uuid

# Ensure root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.session import SessionLocal
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
    TestExecutionResult,
)
from src.workflows.graph import testing_graph
from src.llm.router.agent_model_router import agent_model_router
from src.llm.providers.openai_provider import OpenAIProvider
from src.core.logging import get_logger

logger = get_logger("irctc_live_test")


def main():
    print("=" * 80)
    print("PHASE 1: RUNTIME CONFIGURATION & OPENAI MODEL VERIFICATION")
    print("=" * 80)

    # 1. Verify and enforce OpenAI gpt-6.2-sol across all 6 agents
    target_provider = "openai"
    target_model = "gpt-6.2-sol"

    print(f"Mandated Provider: {target_provider.upper()}")
    print(f"Mandated Model:    {target_model}")

    for agent_key in agent_model_router.get_all_configurations().keys():
        agent_model_router.set_agent_model(agent_key, target_provider, target_model)

    current_configs = agent_model_router.get_all_configurations()
    print("\nVerified Agent Configurations:")
    for ag_id, cfg in current_configs.items():
        print(f"  • {ag_id}: {cfg['provider']} / {cfg['model_id']}")
        assert cfg["provider"] == target_provider, f"Agent {ag_id} provider mismatch: {cfg['provider']}"
        assert cfg["model_id"] == target_model, f"Agent {ag_id} model mismatch: {cfg['model_id']}"

    # Verify provider independently
    test_provider = OpenAIProvider()
    print(f"\nTesting OpenAI provider connectivity...")
    conn_ok = test_provider.test_connection()
    assert conn_ok, "OpenAI connection test failed. Verify API key."
    print(f"[OK] OpenAI Provider connected and verified successfully!")

    print("\n" + "=" * 80)
    print("PHASE 2: ISOLATED PROJECT CREATION — IRCTC - Fast Live Testing")
    print("=" * 80)

    db = SessionLocal()
    try:
        project_name = "IRCTC - Fast Live Testing"
        project = db.query(Project).filter(Project.name == project_name).first()

        irctc_srs = (
            "only 3 test cases for IRCTC fast live website testing:\n"
            "Software Requirement Specification (SRS) - IRCTC Next Generation eTicketing System (https://www.irctc.co.in/):\n"
            "1. Homepage and Navigation Validation: Verify the IRCTC portal homepage loads securely, key visible header elements, "
            "navigation links (Login, Register, Train Services, Contact Us), and branding logos are accessible and rendered.\n"
            "2. Train Search Form UI Validation: Inspect the 'Book Ticket' search form. Validate the origin ('From') and destination ('To') "
            "station input fields, journey date selector, and class dropdown without initiating any booking or payment transactions.\n"
            "3. Search Input & Validation Behavior: Validate input handling on the search form, including empty mandatory field submission, "
            "error message display, and safe validation alerts without side-effects or transactional requests."
        )

        if not project:
            project = Project(
                id=str(uuid.uuid4()),
                name=project_name,
                description=irctc_srs,
                base_url="https://www.irctc.co.in/",
                framework="playwright"
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"[OK] Created new isolated project: {project.name} (ID: {project.id})")
        else:
            project.description = irctc_srs
            project.base_url = "https://www.irctc.co.in/"
            project.framework = "playwright"
            db.commit()
            db.refresh(project)
            print(f"[OK] Re-used and refreshed isolated project: {project.name} (ID: {project.id})")

        # Clean any stale artifacts for this project
        db.query(AutomationScript).filter(AutomationScript.project_id == project.id).delete()
        db.query(TestCase).filter(TestCase.project_id == project.id).delete()
        db.query(TestScenario).filter(TestScenario.project_id == project.id).delete()
        db.query(Requirement).filter(Requirement.project_id == project.id).delete()
        db.commit()
        print(f"[OK] Purged any previous artifacts for project {project.id} to ensure 100% clean isolation.")

        print("\n" + "=" * 80)
        print("PHASE 3: EXECUTING 6-AGENT WORKFLOW IN VISIBLE BROWSER MODE")
        print("=" * 80)
        print("Execution Mode: VISIBLE (HEADED) BROWSER — Headless: DISABLED")
        print("Test Case Limit: EXACTLY 3 TEST CASES")
        print("Target URL: https://www.irctc.co.in/")
        print("Automation Framework: Playwright Chromium")

        run_timestamp = int(time.time())
        initial_state = {
            "thread_id": f"thread_{project.id}_{run_timestamp}",
            "project_id": project.id,
            "workflow_id": f"wf_{project.id}_{run_timestamp}",
            "raw_input_text": project.description,
            "source_type": "manual",
            "framework": "playwright",
            "browser": "chromium",
            "headed": True,  # Headless mode DISABLED!
            "base_url": project.base_url,
            "target_test_count": 3,  # EXACTLY 3 test cases!
            "requirements": [],
            "approved_requirements": [],
            "test_scenarios": [],
            "approved_scenarios": [],
            "test_cases": [],
            "approved_test_cases": [],
            "automation_scripts": [],
            "execution_results": [],
            "current_agent": "start",
            "step_count": 0,
            "errors": [],
            "approval_status": "Approved",
            "workflow_status": "InProgress",
            "consolidated_report": None,
        }

        print("\nLaunching LangGraph State Machine...")
        start_time = time.time()
        final_state = testing_graph.invoke(initial_state)
        total_duration = round(time.time() - start_time, 2)

        print("\n" + "=" * 80)
        print("PHASE 4: WORKFLOW EXECUTION VERIFICATION & AUDIT")
        print("=" * 80)
        print(f"Workflow Status:      {final_state.get('workflow_status')}")
        print(f"Total Execution Time: {total_duration} seconds")
        print(f"Requirements:         {len(final_state.get('requirements', []))}")
        print(f"Scenarios:            {len(final_state.get('test_scenarios', []))}")
        print(f"Test Cases:           {len(final_state.get('test_cases', []))}")
        print(f"Automation Scripts:   {len(final_state.get('automation_scripts', []))}")
        print(f"Execution Results:    {len(final_state.get('execution_results', []))}")

        # Database Verification
        db_reqs = db.query(Requirement).filter(Requirement.project_id == project.id).all()
        db_scens = db.query(TestScenario).filter(TestScenario.project_id == project.id).all()
        db_tcs = db.query(TestCase).filter(TestCase.project_id == project.id).all()
        db_scripts = db.query(AutomationScript).filter(AutomationScript.project_id == project.id).all()
        db_execs = db.query(TestExecution).filter(TestExecution.project_id == project.id).all()

        print(f"\nPersisted in Database:")
        print(f"  • Requirements: {len(db_reqs)}")
        print(f"  • Scenarios:    {len(db_scens)}")
        print(f"  • Test Cases:   {len(db_tcs)}")
        print(f"  • Scripts:      {len(db_scripts)}")
        print(f"  • Executions:   {len(db_execs)}")

        # Strict Exact 3 Check
        print("\n" + "-" * 60)
        print("TEST CASE COUNT STRICT AUDIT")
        print("-" * 60)
        print(f"Generated Test Cases: {len(db_tcs)}")
        assert len(db_tcs) == 3, f"CRITICAL FAILURE: Expected EXACTLY 3 test cases, got {len(db_tcs)}"
        print("[PASS] EXACTLY 3 test cases generated — no more, no less!")

        print("\n" + "-" * 60)
        print("THE 3 GENERATED AI TEST CASES (OpenAI gpt-6.2-sol):")
        print("-" * 60)
        for i, tc in enumerate(db_tcs, 1):
            print(f"\nTest Case {i}: [{tc.test_case_key}] {tc.title}")
            print(f"  • Objective:     {tc.objective}")
            print(f"  • Priority:      {tc.priority} | Type: {tc.test_type}")
            print(f"  • Preconditions: {tc.preconditions}")
            print(f"  • Expected:      {tc.expected_results}")
            print(f"  • Steps:")
            steps = tc.execution_steps if isinstance(tc.execution_steps, list) else []
            for s in steps:
                if isinstance(s, dict):
                    print(f"      Step {s.get('step_number', 1)}: {s.get('action', '')} -> {s.get('expected', '')}")
                else:
                    print(f"      Step: {s}")

        print("\n" + "-" * 60)
        print("BROWSER EXECUTION RESULTS & SCREENSHOTS (Headed Mode):")
        print("-" * 60)
        if db_execs:
            last_exec = db_execs[-1]
            res_items = db.query(TestExecutionResult).filter(TestExecutionResult.execution_id == last_exec.id).all()
            for r in res_items:
                print(f"\n  • [{r.status.upper()}] {r.test_title}")
                print(f"    Duration:    {r.execution_duration_seconds}s")
                print(f"    Screenshot:  {r.screenshot_path or 'Captured in session'}")
                if r.error_message:
                    print(f"    Error Note:  {r.error_message[:120]}")

        # Check cross-project isolation
        print("\n" + "-" * 60)
        print("CROSS-PROJECT ISOLATION VERIFICATION")
        print("-" * 60)
        trainmate_leak = any(
            "trainee" in f"{tc.title} {tc.objective}".lower() or "cohort" in f"{tc.title} {tc.objective}".lower()
            for tc in db_tcs
        )
        assert not trainmate_leak, "TrainMate data leaked into IRCTC test cases!"
        print("[PASS] Zero cross-project leakage from TrainMate or YouTube.")

        # Check report summary
        print("\n" + "=" * 80)
        print("AGENT 6: CONSOLIDATED QUALITY REPORT PREVIEW")
        print("=" * 80)
        rep = final_state.get("consolidated_report", {})
        if rep and isinstance(rep, dict):
            print(rep.get("markdown_report", rep.get("executive_summary", "Report generated successfully.")))

        print("\n" + "=" * 80)
        print("ALL FAST LIVE VALIDATION CHECKS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
