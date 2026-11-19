"""
End-to-End Workflow Test for the 6-Agent Testing Pipeline.
Tests the complete LangGraph execution from requirements to consolidated reporting.
"""

import pytest
from src.database.session import SessionLocal
from src.models.entities import Project
from src.workflows.graph import testing_graph


def test_full_6_agent_workflow_e2e():
    # 1. Setup project
    with SessionLocal() as db:
        p = Project(
            name="E2E Pipeline Project",
            description="End-to-end checkout flow validation with credit card.",
            framework="playwright",
            base_url="http://127.0.0.1:8000",
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        project_id = p.id

    # 2. Trigger pipeline state
    initial_state = {
        "thread_id": f"thread_{project_id}",
        "project_id": project_id,
        "workflow_id": f"wf_{project_id}",
        "raw_input_text": (
            "Feature: Checkout and Payment\n"
            "As a customer, I want to pay with credit card.\n"
            "Acceptance Criteria:\n"
            "1. Card number must be 16 digits.\n"
            "2. Successful payment shows confirmation and order number within 2 seconds.\n"
            "3. Expired cards are rejected with 'Card expired' error message."
        ),
        "source_type": "manual",
        "framework": "playwright",
        "base_url": "http://127.0.0.1:8000",
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

    # 3. Execute LangGraph workflow
    final_state = testing_graph.invoke(initial_state)

    # 4. Verify outcomes across all 6 agents
    assert final_state["workflow_status"] == "Completed"
    assert final_state["current_agent"] == "agent_6_orchestration_reporting"

    # Agent 1 check
    assert len(final_state["requirements"]) > 0

    # Agent 2 check
    assert len(final_state["test_scenarios"]) > 0

    # Agent 3 check
    assert len(final_state["test_cases"]) > 0

    # Agent 4 check
    assert len(final_state["automation_scripts"]) > 0

    # Agent 5 check
    assert len(final_state["execution_results"]) > 0

    # Agent 6 check
    report = final_state["consolidated_report"]
    assert report is not None
    assert report["project_name"] == "E2E Pipeline Project"
    assert report["requirement_coverage_pct"] > 0
    assert "Executive Summary" in report["markdown_report"]
