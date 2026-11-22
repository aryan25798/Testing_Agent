"""
Pydantic Schemas and DTOs for Model Context Protocol (MCP) Integration.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MCPServerStatusDTO(BaseModel):
    provider: str
    server_name: str
    transport: str  # stdio | sse
    server_url: Optional[str] = None
    account_login: Optional[str] = None
    account_name: Optional[str] = None
    status: str     # connected | disconnected | connecting | error
    is_read_only: bool = True
    available_tools_count: int = 0
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None


class ConnectGitHubRequest(BaseModel):
    method: str = Field(default="stdio", pattern="^(stdio|remote)$")
    token: Optional[str] = Field(default=None, description="GitHub Personal Access Token (PAT)")
    selected_repositories: List[str] = Field(default_factory=list)


class ConnectJiraRequest(BaseModel):
    method: str = Field(default="stdio", pattern="^(stdio|sse)$")
    host_url: str = Field(..., description="e.g. https://your-domain.atlassian.net")
    email: str = Field(..., description="Atlassian Account Email")
    api_token: Optional[str] = Field(default=None, description="Atlassian API Token")
    selected_projects: List[str] = Field(default_factory=list)


class MCPToolInfoDTO(BaseModel):
    server_provider: str
    tool_name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    is_read_only: bool = True
    allowed_agents: List[str] = Field(default_factory=list)
    risk_level: str = "low"


class ProjectMCPMappingDTO(BaseModel):
    project_id: str
    provider: str
    external_id: str  # owner/repo or Jira host URL
    selected_resources: List[str] = Field(default_factory=list)
    default_branch: str = "main"
    status: str = "active"
    last_synced_at: Optional[datetime] = None


class ProjectMCPMappingRequest(BaseModel):
    github_repo: Optional[str] = None
    github_branch: Optional[str] = "main"
    jira_host: Optional[str] = None
    jira_project_keys: List[str] = Field(default_factory=list)
    jira_key: Optional[str] = None
    provider: Optional[str] = None
    external_id: Optional[str] = None
    selected_resources: List[str] = Field(default_factory=list)
    default_branch: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    reason: Optional[str] = None


class MCPApprovalRequestDTO(BaseModel):
    id: str
    project_id: str
    provider: str
    agent_id: str
    tool_name: str
    target_object: str
    operation_description: str
    proposed_diff: Optional[str] = None
    risk_level: str
    status: str
    created_at: datetime
    decided_at: Optional[datetime] = None
    decision_reason: Optional[str] = None


class MCPToolInvocationLogDTO(BaseModel):
    id: str
    server_provider: str
    agent_id: str
    tool_name: str
    operation_type: str
    status: str
    duration_seconds: float
    arguments_summary: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime
