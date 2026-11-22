"""
LangGraph Shared Typed Workflow State.
Tracks data transfer and approval barriers between all 6 specialized testing agents.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class TestingWorkflowState(TypedDict):
    thread_id: str
    project_id: str
    workflow_id: str
    raw_input_text: str
    source_type: str  # manual | file | jira
    framework: str    # playwright | selenium
    browser: Optional[str]  # chromium | firefox | webkit | chrome
    base_url: str

    # Artifacts passed between agents
    requirements: List[Dict[str, Any]]
    approved_requirements: List[Dict[str, Any]]
    test_scenarios: List[Dict[str, Any]]
    approved_scenarios: List[Dict[str, Any]]
    test_cases: List[Dict[str, Any]]
    approved_test_cases: List[Dict[str, Any]]
    automation_scripts: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]

    # Observability & Tracking
    current_agent: str
    step_count: int
    errors: List[str]
    approval_status: str  # Pending | Approved | Rejected
    workflow_status: str  # InProgress | WaitingForApproval | Completed | Failed
    consolidated_report: Optional[Dict[str, Any]]
