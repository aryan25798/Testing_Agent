"""
FastAPI REST Endpoints for Model Context Protocol (MCP) Integration Center.
Provides full connection wizards, repository & Jira discovery, dynamic tool inspection,
project-level integration mappings, and human approval gates.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from src.integrations.mcp.models import (
    MCPServerStatusDTO,
    ConnectGitHubRequest,
    ConnectJiraRequest,
    ProjectMCPMappingRequest,
    ProjectMCPMappingDTO,
    ApprovalDecisionRequest,
    MCPApprovalRequestDTO,
    MCPToolInfoDTO,
    MCPToolInvocationLogDTO,
)
from src.integrations.mcp.connection_manager import mcp_connection_manager
from src.integrations.mcp.tool_registry import tool_registry
from src.integrations.mcp.approval_manager import approval_manager
from src.database.session import SessionLocal
from src.models.entities import (
    MCPServerConnection,
    MCPDiscoveredTool,
    ProjectIntegrationMapping,
    MCPToolInvocationLog,
    Project,
)
from src.core.security.audit_logger import audit_logger
from src.core.security.sanitizer import prompt_sanitizer

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/servers", response_model=List[MCPServerStatusDTO])
def get_all_mcp_servers():
    """Returns real, live connection and tool discovery statuses for GitHub and Atlassian."""
    return mcp_connection_manager.get_all_servers_status()


@router.post("/github/connect")
async def connect_github_mcp(payload: ConnectGitHubRequest):
    """
    Connects to official GitHub MCP Server via stdio.
    Negotiates capabilities, discovers real tool schemas, and registers them dynamically.
    """
    try:
        res = await mcp_connection_manager.connect_and_discover_github(token=payload.token)
        return {
            "status": "connected",
            "provider": "github",
            "server_name": res["server_name"],
            "tools_count": res["tools_count"],
            "duration_seconds": res["duration_seconds"],
            "message": f"Successfully connected to GitHub MCP Server. Discovered {res['tools_count']} tools.",
        }
    except Exception as e:
        safe_msg = prompt_sanitizer.redact_secrets(str(e))
        raise HTTPException(status_code=400, detail=safe_msg)


@router.post("/atlassian/connect")
async def connect_atlassian_mcp(payload: ConnectJiraRequest):
    """
    Connects to Atlassian Jira MCP Server (stdio or official remote SSE).
    Negotiates capabilities, discovers real tool schemas, and registers them dynamically.
    """
    try:
        res = await mcp_connection_manager.connect_and_discover_jira(
            host_url=payload.host_url,
            email=payload.email,
            token=payload.api_token,
            method=payload.method,
        )
        return {
            "status": "connected",
            "provider": "atlassian",
            "server_name": res["server_name"],
            "tools_count": res["tools_count"],
            "duration_seconds": res["duration_seconds"],
            "message": f"Successfully connected to Atlassian Jira MCP Server. Discovered {res['tools_count']} tools.",
        }
    except Exception as e:
        safe_msg = prompt_sanitizer.redact_secrets(str(e))
        raise HTTPException(status_code=400, detail=safe_msg)


@router.post("/servers/{provider}/disconnect")
def disconnect_mcp_server(provider: str):
    """Gracefully terminates connection to target MCP server."""
    prov_clean = provider.lower().strip()
    return mcp_connection_manager.disconnect(prov_clean)


@router.get("/tools", response_model=List[MCPToolInfoDTO])
@router.get("/servers/{provider}/tools", response_model=List[MCPToolInfoDTO])
def list_discovered_mcp_tools(provider: Optional[str] = None):
    """Lists dynamically discovered tool schemas and per-agent permissions."""
    tools = tool_registry.get_registered_tools(provider)
    return [
        MCPToolInfoDTO(
            server_provider=t.get("server_provider") or (provider.lower() if provider else "mcp"),
            tool_name=t["tool_name"],
            description=t["description"],
            input_schema=t["input_schema"],
            is_read_only=t["is_read_only"],
            allowed_agents=t["allowed_agents"],
            risk_level=t["risk_level"],
        )
        for t in tools
    ]


@router.get("/github/repositories")
async def discover_github_repositories():
    """
    Invokes GitHub MCP tool search_repositories to discover user-accessible repositories.
    """
    try:
        res = await mcp_connection_manager.execute_tool(
            provider="github",
            tool_name="search_repositories",
            arguments={"query": "user:@me", "per_page": 30},
        )
        return {"provider": "github", "raw_discovery": res}
    except Exception as e:
        safe_err = prompt_sanitizer.redact_secrets(str(e))
        raise HTTPException(status_code=400, detail=safe_err)


@router.get("/jira/projects")
async def discover_jira_projects():
    """
    Invokes Atlassian Jira MCP tool jira_get_user_profile or jira_search to discover accessible projects.
    """
    try:
        res = await mcp_connection_manager.execute_tool(
            provider="atlassian",
            tool_name="jira_get_user_profile",
            arguments={},
        )
        return {"provider": "atlassian", "raw_discovery": res}
    except Exception as e:
        safe_err = prompt_sanitizer.redact_secrets(str(e))
        raise HTTPException(status_code=400, detail=safe_err)


# --- Project Integration Mapping ---

@router.get("/projects/{project_id}/mapping")
def get_project_mcp_mapping(project_id: str):
    """Returns active GitHub and Jira MCP integration mappings for a project."""
    with SessionLocal() as db:
        mappings = (
            db.query(ProjectIntegrationMapping)
            .filter(ProjectIntegrationMapping.project_id == project_id)
            .all()
        )
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        result = {
            "project_id": project_id,
            "project_name": proj.name,
            "github_mapping": None,
            "jira_mapping": None,
        }

        for m in mappings:
            data = {
                "id": m.id,
                "external_id": m.external_id,
                "selected_resources": m.selected_resources or [],
                "default_branch": m.default_branch,
                "status": m.status,
                "last_synced_at": m.last_synced_at.isoformat() if m.last_synced_at else None,
            }
            if m.provider == "github":
                result["github_mapping"] = data
            elif m.provider == "atlassian":
                result["jira_mapping"] = data

        return result


@router.post("/projects/{project_id}/mapping")
def update_project_mcp_mapping(project_id: str, payload: ProjectMCPMappingRequest):
    """Maps selected GitHub repository and Jira projects to the internal project."""
    with SessionLocal() as db:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. GitHub Mapping
        if payload.github_repo:
            gh_server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
            if gh_server:
                gh_mapping = (
                    db.query(ProjectIntegrationMapping)
                    .filter(
                        ProjectIntegrationMapping.project_id == project_id,
                        ProjectIntegrationMapping.provider == "github",
                    )
                    .first()
                )
                if not gh_mapping:
                    gh_mapping = ProjectIntegrationMapping(
                        project_id=project_id,
                        server_id=gh_server.id,
                        provider="github",
                        external_id=payload.github_repo,
                    )
                    db.add(gh_mapping)

                gh_mapping.external_id = payload.github_repo
                gh_mapping.selected_resources = [payload.github_repo]
                gh_mapping.default_branch = payload.github_branch or "main"
                gh_mapping.status = "active"

                # Update project table for synchronization
                proj.git_repo_url = f"https://github.com/{payload.github_repo}"
                proj.git_branch = payload.github_branch or "main"

        # 2. Jira Mapping
        if payload.jira_host or payload.jira_project_keys:
            atl_server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "atlassian").first()
            if atl_server:
                atl_mapping = (
                    db.query(ProjectIntegrationMapping)
                    .filter(
                        ProjectIntegrationMapping.project_id == project_id,
                        ProjectIntegrationMapping.provider == "atlassian",
                    )
                    .first()
                )
                if not atl_mapping:
                    atl_mapping = ProjectIntegrationMapping(
                        project_id=project_id,
                        server_id=atl_server.id,
                        provider="atlassian",
                        external_id=payload.jira_host or atl_server.server_url or "https://atlassian.net",
                    )
                    db.add(atl_mapping)

                atl_mapping.external_id = payload.jira_host or atl_server.server_url or "https://atlassian.net"
                atl_mapping.selected_resources = payload.jira_project_keys
                atl_mapping.status = "active"

                if payload.jira_project_keys:
                    proj.jira_project_key = payload.jira_project_keys[0]

        db.commit()

        audit_logger.log_event(
            action="PROJECT_MCP_MAPPING_UPDATED",
            status="SUCCESS",
            details={
                "project_id": project_id,
                "github_repo": payload.github_repo,
                "jira_projects": payload.jira_project_keys,
            },
        )

        return {"status": "success", "message": "Project MCP integration mapping updated successfully."}


# --- Human Approvals for Mutating MCP Tools ---

@router.get("/approvals/pending", response_model=List[MCPApprovalRequestDTO])
def list_pending_mcp_approvals(project_id: Optional[str] = None):
    """Returns all pending approval requests awaiting human consent."""
    approvals = approval_manager.get_pending_approvals(project_id)
    return approvals


@router.post("/approvals/{approval_id}/decision")
def record_approval_decision(approval_id: str, payload: ApprovalDecisionRequest):
    """Records human engineer approval or rejection of a proposed mutating operation."""
    try:
        res = approval_manager.decide_approval(
            approval_id=approval_id,
            decision=payload.decision,
            reason=payload.reason,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Audit Logs ---

@router.get("/logs", response_model=List[MCPToolInvocationLogDTO])
def get_mcp_tool_logs(provider: Optional[str] = None, limit: int = 50):
    """Returns tamper-evident MCP invocation log with confidential payloads redacted."""
    with SessionLocal() as db:
        query = db.query(MCPToolInvocationLog)
        if provider:
            query = query.filter(MCPToolInvocationLog.server_id == provider)
        records = query.order_by(MCPToolInvocationLog.timestamp.desc()).limit(limit).all()

        return [
            MCPToolInvocationLogDTO(
                id=r.id,
                server_provider=r.server_id,
                agent_id=r.agent_id,
                tool_name=r.tool_name,
                operation_type=r.operation_type,
                status=r.status,
                duration_seconds=r.duration_seconds,
                arguments_summary=r.arguments_summary or {},
                error_message=r.error_message,
                timestamp=r.timestamp,
            )
            for r in records
        ]
