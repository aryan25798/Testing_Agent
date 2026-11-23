"""
Pydantic V2 Data Transfer Objects (DTOs) & Schemas.
Enforces strict typing and data validation across the platform.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    framework: str = Field(default="playwright")  # selenium | playwright
    jira_project_key: Optional[str] = None
    git_repo_url: Optional[str] = None
    git_branch: str = "main"
    base_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementBase(BaseModel):
    requirement_key: str
    source_type: str = "manual"
    title: str
    description: str
    business_objective: Optional[str] = None
    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    risk_level: str = "Medium"
    priority: str = "Medium"
    testability_status: str = "Testable"
    is_approved: bool = False
    approval_notes: Optional[str] = None


class RequirementCreate(RequirementBase):
    project_id: str


class RequirementRead(RequirementBase):
    id: str
    project_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestScenarioBase(BaseModel):
    __test__ = False
    scenario_key: str
    title: str
    description: str
    test_type: str = "Functional"
    preconditions: Optional[str] = None
    test_objective: Optional[str] = None
    priority: str = "Medium"
    risk: str = "Medium"
    expected_outcome: str
    automation_suitability: str = "Yes"
    is_approved: bool = False


class TestScenarioCreate(TestScenarioBase):
    __test__ = False
    project_id: str
    requirement_id: str


class TestScenarioRead(TestScenarioBase):
    __test__ = False
    id: str
    project_id: str
    requirement_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestCaseStep(BaseModel):
    step_number: int
    action: str
    expected: str


class TestCaseBase(BaseModel):
    __test__ = False
    test_case_key: str
    title: str
    objective: str
    test_type: str = "Functional"
    priority: str = "Medium"
    preconditions: Optional[str] = None
    test_environment: str = "QA"
    test_data: Dict[str, Any] = Field(default_factory=dict)
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    expected_results: str
    actual_results: Optional[str] = None
    status: str = "Draft"
    automation_suitability: str = "Yes"
    tags: List[str] = Field(default_factory=list)
    is_approved: bool = False


class TestCaseCreate(TestCaseBase):
    __test__ = False
    project_id: str
    scenario_id: str
    requirement_id: str


class TestCaseRead(TestCaseBase):
    __test__ = False
    id: str
    project_id: str
    scenario_id: str
    requirement_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutomationScriptBase(BaseModel):
    framework: str
    script_name: str
    file_path: str
    code_content: str
    language: str = "python"
    syntax_valid: bool = True
    is_approved: bool = False


class AutomationScriptCreate(AutomationScriptBase):
    project_id: str
    test_case_id: Optional[str] = None


class AutomationScriptRead(AutomationScriptBase):
    id: str
    project_id: str
    test_case_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestExecutionCreate(BaseModel):
    __test__ = False
    project_id: str
    runner_type: str = "playwright"
    target_environment: str = "QA"
    base_url: Optional[str] = None
    browser: str = "chrome"
    test_case_ids: Optional[List[str]] = None


class TestExecutionResultRead(BaseModel):
    __test__ = False
    id: str
    test_case_id: Optional[str] = None
    test_title: str
    status: str
    failing_step: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    failure_classification: Optional[str] = None
    suggested_fix: Optional[str] = None
    execution_duration_seconds: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TestExecutionRead(BaseModel):
    __test__ = False
    id: str
    project_id: str
    execution_key: str
    runner_type: str
    target_environment: str
    base_url: Optional[str] = None
    browser: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    blocked_tests: int
    execution_duration_seconds: float
    status: str
    created_at: datetime
    results: List[TestExecutionResultRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecision(BaseModel):
    status: str = Field(..., pattern="^(Approved|Rejected)$")
    decision_reason: Optional[str] = None


class ApprovalRequestRead(BaseModel):
    id: str
    project_id: str
    action_type: str
    requested_by: str
    details: Dict[str, Any]
    status: str
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelInfo(BaseModel):
    model_id: str
    provider: str
    display_name: str
    context_window: int
    supports_tools: bool
    supports_vision: bool
    is_available: bool = True
    description: Optional[str] = None


class AgentModelConfig(BaseModel):
    agent_id: str
    agent_name: str
    provider: str
    model_id: str


class JiraConnectRequest(BaseModel):
    host_url: str
    email: str
    api_token: str
    project_key: Optional[str] = None


class GitConnectRequest(BaseModel):
    provider: str = "github"
    host_url: str = "https://github.com"
    token: str
    repo_url: Optional[str] = None
    branch: str = "main"


class WorkflowStartRequest(BaseModel):
    project_id: str
    source_type: str = "manual"  # manual | file | jira
    requirements_text: Optional[str] = None
    file_path: Optional[str] = None
    jira_issue_keys: Optional[List[str]] = None
    framework: str = "playwright"
    browser: str = "chromium"  # chromium | firefox | webkit | chrome
    headed: bool = False  # Headed / Watch mode toggle


class BulkDeleteRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1)


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    deleted_ids: List[str]
    failed_ids: List[str] = Field(default_factory=list)
    message: str


class BulkApproveRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1)


class BulkApproveResponse(BaseModel):
    approved_count: int
    approved_ids: List[str]
    message: str


class PaginatedProjectsResponse(BaseModel):
    items: List[ProjectRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedTestCasesResponse(BaseModel):
    items: List[TestCaseRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedExecutionsResponse(BaseModel):
    items: List[TestExecutionRead]
    total: int
    page: int
    page_size: int
    total_pages: int

