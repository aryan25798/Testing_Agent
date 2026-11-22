"""
SQLAlchemy ORM Models for Testing Agent Platform.
Provides complete relational persistence for testing lifecycle entities.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from src.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    framework = Column(String(50), default="playwright")  # selenium | playwright
    jira_project_key = Column(String(100), nullable=True)
    git_repo_url = Column(String(255), nullable=True)
    git_branch = Column(String(100), default="main")
    base_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    test_scenarios = relationship("TestScenario", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    automation_scripts = relationship("AutomationScript", back_populates="project", cascade="all, delete-orphan")
    executions = relationship("TestExecution", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("ApprovalRequest", back_populates="project", cascade="all, delete-orphan")
    agent_executions = relationship("AgentExecution", back_populates="project", cascade="all, delete-orphan")
    integration_mappings = relationship("ProjectIntegrationMapping", back_populates="project", cascade="all, delete-orphan")
    mcp_approvals = relationship("MCPApprovalRequest", back_populates="project", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "requirement_key", name="uq_req_project_key"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    requirement_key = Column(String(100), nullable=False)  # REQ-001 or JIRA-101
    source_type = Column(String(50), default="manual")     # jira, file, manual
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    business_objective = Column(Text, nullable=True)
    functional_requirements = Column(JSON, default=list)
    non_functional_requirements = Column(JSON, default=list)
    acceptance_criteria = Column(JSON, default=list)
    business_rules = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    missing_information = Column(JSON, default=list)
    clarification_questions = Column(JSON, default=list)
    risk_level = Column(String(50), default="Medium")      # Low, Medium, High, Critical
    priority = Column(String(50), default="Medium")        # Low, Medium, High, Critical
    testability_status = Column(String(50), default="Testable")
    is_approved = Column(Boolean, default=False)
    approval_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="requirements")
    test_scenarios = relationship("TestScenario", back_populates="requirement", cascade="all, delete-orphan")


class TestScenario(Base):
    __tablename__ = "test_scenarios"
    __table_args__ = (
        UniqueConstraint("project_id", "scenario_key", name="uq_scen_project_key"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False, index=True)
    scenario_key = Column(String(100), nullable=False)     # SCEN-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    test_type = Column(String(100), default="Functional")  # Positive, Negative, Boundary, Security, etc.
    preconditions = Column(Text, nullable=True)
    test_objective = Column(Text, nullable=True)
    priority = Column(String(50), default="Medium")
    risk = Column(String(50), default="Medium")
    expected_outcome = Column(Text, nullable=False)
    automation_suitability = Column(String(50), default="Yes") # Yes, No, Partial
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="test_scenarios")
    requirement = relationship("Requirement", back_populates="test_scenarios")
    test_cases = relationship("TestCase", back_populates="scenario", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        UniqueConstraint("project_id", "test_case_key", name="uq_tc_project_key"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    scenario_id = Column(String(36), ForeignKey("test_scenarios.id"), nullable=False, index=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False, index=True)
    test_case_key = Column(String(100), nullable=False)    # TC-001
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    test_type = Column(String(100), default="Functional")
    priority = Column(String(50), default="Medium")
    preconditions = Column(Text, nullable=True)
    test_environment = Column(String(100), default="QA")
    test_data = Column(JSON, default=dict)
    execution_steps = Column(JSON, default=list)          # [{"step_number": 1, "action": "...", "expected": "..."}]
    expected_results = Column(Text, nullable=False)
    actual_results = Column(Text, nullable=True)
    status = Column(String(50), default="Draft")          # Draft, Approved, Deprecated
    automation_suitability = Column(String(50), default="Yes")
    tags = Column(JSON, default=list)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="test_cases")
    scenario = relationship("TestScenario", back_populates="test_cases")
    automation_scripts = relationship("AutomationScript", back_populates="test_case", cascade="all, delete-orphan")


class AutomationScript(Base):
    __tablename__ = "automation_scripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=True, index=True)
    framework = Column(String(50), nullable=False)        # selenium | playwright
    script_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    code_content = Column(Text, nullable=False)
    language = Column(String(50), default="python")
    syntax_valid = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="automation_scripts")
    test_case = relationship("TestCase", back_populates="automation_scripts")


class TestExecution(Base):
    __tablename__ = "test_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    execution_key = Column(String(100), nullable=False)   # RUN-001
    runner_type = Column(String(50), default="playwright")
    target_environment = Column(String(100), default="QA")
    base_url = Column(String(255), nullable=True)
    browser = Column(String(50), default="chrome")
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    blocked_tests = Column(Integer, default=0)
    execution_duration_seconds = Column(Float, default=0.0)
    status = Column(String(50), default="Pending")        # Pending, Running, Completed, Failed, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="executions")
    results = relationship("TestExecutionResult", back_populates="execution", cascade="all, delete-orphan")


class TestExecutionResult(Base):
    __tablename__ = "test_execution_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("test_executions.id"), nullable=False, index=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=True, index=True)
    test_title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)           # Passed, Failed, Skipped, Blocked, Error
    failing_step = Column(String(255), nullable=True)
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    screenshot_path = Column(String(255), nullable=True)
    trace_path = Column(String(255), nullable=True)
    log_output = Column(Text, nullable=True)
    failure_classification = Column(String(100), nullable=True) # ApplicationDefect, EnvironmentIssue, FlakyTest
    suggested_fix = Column(Text, nullable=True)
    execution_duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("TestExecution", back_populates="results")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)     # git_write, execute_test, delete_data, prod_run
    requested_by = Column(String(100), default="System")
    details = Column(JSON, default=dict)
    status = Column(String(50), default="Pending")        # Pending, Approved, Rejected
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="approvals")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    agent_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_seconds = Column(Float, default=0.0)
    status = Column(String(50), default="Success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="agent_executions")


class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    integration_type = Column(String(50), nullable=False) # jira, git, mcp
    name = Column(String(255), nullable=False)
    host_url = Column(String(255), nullable=True)
    auth_type = Column(String(50), default="token")
    username_or_email = Column(String(255), nullable=True)
    masked_secret = Column(String(255), nullable=True)
    raw_secret_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=True)
    actor = Column(String(100), default="User")
    action = Column(String(100), nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="Specialized QA")
    system_instructions = Column(Text, nullable=False)
    provider = Column(String(50), default="gemini")
    model_id = Column(String(100), default="gemini-2.5-flash")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- MCP (Model Context Protocol) Entities ---

class MCPServerConnection(Base):
    __tablename__ = "mcp_server_connections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(50), nullable=False)           # github | atlassian
    server_name = Column(String(255), nullable=False)       # "Official GitHub MCP Server", "Atlassian Remote MCP Server"
    transport = Column(String(50), default="stdio")         # stdio | sse | streamable-http
    server_url = Column(String(500), nullable=True)         # Remote URL e.g. https://mcp.atlassian.com/v2/mcp
    command = Column(Text, nullable=True)                   # Local command array or binary path
    auth_type = Column(String(50), default="pat")           # pat | oauth2 | token
    account_login = Column(String(255), nullable=True)      # e.g. "aryan25798" or "aryan@company.com"
    account_name = Column(String(255), nullable=True)       # Display Name
    status = Column(String(50), default="disconnected")     # connected | disconnected | error | connecting
    is_read_only = Column(Boolean, default=True)            # Enforce read-only by default
    capabilities = Column(JSON, default=dict)               # Negotiated capabilities
    last_connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tools = relationship("MCPDiscoveredTool", back_populates="server", cascade="all, delete-orphan")
    mappings = relationship("ProjectIntegrationMapping", back_populates="server", cascade="all, delete-orphan")


class MCPDiscoveredTool(Base):
    __tablename__ = "mcp_discovered_tools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("mcp_server_connections.id"), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSON, default=dict)
    is_read_only = Column(Boolean, default=True)
    allowed_agents = Column(JSON, default=list)             # List of agent IDs allowed to invoke this tool
    risk_level = Column(String(50), default="low")          # low | medium | high | critical
    discovered_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("MCPServerConnection", back_populates="tools")


class ProjectIntegrationMapping(Base):
    __tablename__ = "project_integration_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("mcp_server_connections.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)           # github | atlassian
    external_id = Column(String(255), nullable=False)       # e.g. "owner/repo" or "https://domain.atlassian.net"
    selected_resources = Column(JSON, default=list)         # List of repo slugs or Jira project keys
    default_branch = Column(String(100), default="main")
    status = Column(String(50), default="active")           # active | error | paused
    last_synced_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="integration_mappings")
    server = relationship("MCPServerConnection", back_populates="mappings")


class MCPToolInvocationLog(Base):
    __tablename__ = "mcp_tool_invocation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(100), nullable=False)
    tool_name = Column(String(255), nullable=False)
    operation_type = Column(String(50), default="read")     # read | write
    arguments_summary = Column(JSON, default=dict)          # Sanitized arguments without secrets
    status = Column(String(50), default="success")          # success | failed | rejected
    duration_seconds = Column(Float, default=0.0)
    approval_id = Column(String(36), nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MCPApprovalRequest(Base):
    __tablename__ = "mcp_approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)           # github | atlassian
    agent_id = Column(String(100), nullable=False)
    tool_name = Column(String(255), nullable=False)
    arguments = Column(JSON, default=dict)
    target_object = Column(String(255), nullable=False)     # e.g. "repo: aryan25798/app branch: feature/qa"
    operation_description = Column(Text, nullable=False)
    proposed_diff = Column(Text, nullable=True)
    risk_level = Column(String(50), default="medium")       # low | medium | high | critical
    status = Column(String(50), default="pending")          # pending | approved | rejected | expired
    decided_by = Column(String(100), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="mcp_approvals")

