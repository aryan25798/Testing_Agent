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
from src.core.security.secrets_manager import secrets_manager
from src.core.logging import get_logger

logger = get_logger("mcp_api")


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
@router.post("/disconnect/{provider}")
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
async def discover_github_repositories(query: Optional[str] = None):
    """
    Discovers all user-accessible repositories (up to 100+ repos) via GitHub MCP or direct API.
    If query is provided, automatically matches and prioritizes that repository.
    Returns clean array of {name, full_name, private, default_branch} for the UI.
    """
    import json
    repos = []
    login = None

    with SessionLocal() as db:
        server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
        if server and server.account_login:
            login = server.account_login

    token = secrets_manager.get_secret("github")

    # 1. Fetch user repositories via authenticated API (retrieves all 80+ repos)
    if token:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.github.com/user/repos?per_page=100&sort=updated",
                    headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                )
                if res.status_code == 200:
                    raw_repos = res.json()
                    for r in raw_repos:
                        repos.append({
                            "name": r.get("name", ""),
                            "full_name": r.get("full_name") or (f"{login}/{r.get('name')}" if login else r.get("name")),
                            "private": r.get("private", False),
                            "default_branch": r.get("default_branch", "main"),
                        })
        except Exception as e:
            logger.warning(f"Error fetching direct user repos: {e}")

    # 2. Fallback via MCP tool search_repositories
    if not repos:
        try:
            q = f"user:{login}" if login else "user:@me"
            res = await mcp_connection_manager.execute_tool(
                provider="github",
                tool_name="search_repositories",
                arguments={"query": q, "perPage": 100},
                agent_id="orchestrator",
            )
            if res:
                data = json.loads(res) if isinstance(res, str) else res
                items = data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for r in items:
                    repos.append({
                        "name": r.get("name", ""),
                        "full_name": r.get("full_name") or (f"{login}/{r.get('name')}" if login else r.get("name")),
                        "private": r.get("private", False),
                        "default_branch": r.get("default_branch", "main"),
                    })
        except Exception as e:
            logger.warning(f"MCP search_repositories invocation failed: {e}")

    # 3. If query parameter was provided (e.g. repo URL or name), match & prioritize it
    if query:
        clean_q = query.strip().lower()
        if "github.com/" in clean_q:
            clean_q = clean_q.split("github.com/")[-1].replace(".git", "").strip("/")
        matched = [r for r in repos if clean_q in r["full_name"].lower() or clean_q in r["name"].lower()]
        if matched:
            unmatched = [r for r in repos if r not in matched]
            repos = matched + unmatched
        else:
            repo_name = clean_q.split("/")[-1] if "/" in clean_q else clean_q
            full_slug = clean_q if "/" in clean_q else (f"{login}/{clean_q}" if login else clean_q)
            repos.insert(0, {
                "name": repo_name,
                "full_name": full_slug,
                "private": False,
                "default_branch": "main",
            })

    return repos


@router.get("/jira/projects")
async def discover_jira_projects():
    """
    Invokes Atlassian Jira MCP tool jira_get_all_projects to discover accessible projects.
    Returns clean array of {id, key, name} for the UI.
    """
    import json
    projects = []

    try:
        res = await mcp_connection_manager.execute_tool(
            provider="atlassian",
            tool_name="jira_get_all_projects",
            arguments={"include_archived": False},
            agent_id="orchestrator",
        )
        if res:
            data = json.loads(res) if isinstance(res, str) else res
            items = data.get("values", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for p in items:
                if p.get("key"):
                    projects.append({
                        "id": str(p.get("id") or p.get("key")),
                        "key": str(p.get("key")),
                        "name": str(p.get("name") or p.get("key")),
                    })
    except Exception as e:
        logger.warning(f"MCP jira_get_all_projects invocation failed, trying JiraClient fallback: {e}")

    # Fallback via JiraClient REST API if MCP tool returned empty
    if not projects:
        try:
            from src.integrations.jira.jira_client import JiraClient
            from src.core.security.secrets_manager import secrets_vault
            host = secrets_vault.get_secret("JIRA_HOST_URL")
            email = secrets_vault.get_secret("JIRA_EMAIL")
            token = secrets_vault.get_secret("JIRA_API_TOKEN")
            if host and email and token:
                jc = JiraClient(host_url=host, email=email, api_token=token)
                projs = jc.get_projects()
                for p in projs:
                    projects.append({
                        "id": str(p.get("id") or p.get("key")),
                        "key": str(p.get("key")),
                        "name": str(p.get("name") or p.get("key")),
                    })
        except Exception as fallback_err:
            logger.warning(f"JiraClient fallback failed: {fallback_err}")

    return projects


# --- Project Integration Mapping ---

@router.get("/projects/{project_id}/mapping")
def get_project_mcp_mapping(project_id: str, provider: Optional[str] = None):
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
                "project_id": m.project_id,
                "provider": m.provider,
                "external_id": m.external_id,
                "selected_resources": m.selected_resources or ([m.external_id] if m.external_id else []),
                "default_branch": m.default_branch or "main",
                "status": m.status or "active",
                "last_synced_at": m.last_synced_at.isoformat() if m.last_synced_at else None,
            }
            if m.provider == "github":
                result["github_mapping"] = data
            elif m.provider == "atlassian":
                result["jira_mapping"] = data

        # Default fallback to project table fields if explicit mapping row not yet created
        if not result["github_mapping"] and proj.git_repo_url:
            clean_repo = proj.git_repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
            result["github_mapping"] = {
                "id": "direct-project-sync",
                "project_id": project_id,
                "provider": "github",
                "external_id": clean_repo,
                "selected_resources": [clean_repo],
                "default_branch": proj.git_branch or "main",
                "status": "active",
            }

        if not result["jira_mapping"] and proj.jira_project_key:
            result["jira_mapping"] = {
                "id": "direct-project-sync",
                "project_id": project_id,
                "provider": "atlassian",
                "external_id": proj.jira_project_key,
                "selected_resources": [proj.jira_project_key],
                "default_branch": "main",
                "status": "active",
            }

        # If frontend queried a specific provider, return that provider's mapping object directly
        if provider == "github":
            return result["github_mapping"] or {
                "project_id": project_id,
                "provider": "github",
                "external_id": "",
                "selected_resources": [],
                "default_branch": "main",
                "status": "unmapped",
            }
        elif provider == "atlassian":
            return result["jira_mapping"] or {
                "project_id": project_id,
                "provider": "atlassian",
                "external_id": "",
                "selected_resources": [],
                "status": "unmapped",
            }

        return result


@router.post("/projects/{project_id}/mapping")
def update_project_mcp_mapping(project_id: str, payload: ProjectMCPMappingRequest):
    """Maps selected GitHub repository and Jira projects to the internal project and syncs both tables."""
    with SessionLocal() as db:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. Normalize and Save GitHub Repository Mapping
        raw_repo = payload.github_repo
        if not raw_repo and payload.provider == "github":
            raw_repo = payload.external_id or (payload.selected_resources[0] if payload.selected_resources else None)
        elif not raw_repo and payload.external_id and ("/" in str(payload.external_id) or not payload.provider):
            raw_repo = payload.external_id

        if raw_repo:
            clean_repo = str(raw_repo).strip()
            if "github.com/" in clean_repo:
                clean_repo = clean_repo.split("github.com/")[-1]
            clean_repo = clean_repo.replace(".git", "").strip("/")
            branch = payload.github_branch or payload.default_branch or "main"

            gh_server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
            gh_server_id = gh_server.id if gh_server else "github-mcp-server"
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
                    server_id=gh_server_id,
                    provider="github",
                    external_id=clean_repo,
                )
                db.add(gh_mapping)

            gh_mapping.server_id = gh_server_id
            gh_mapping.external_id = clean_repo
            gh_mapping.selected_resources = [clean_repo]
            gh_mapping.default_branch = branch
            gh_mapping.status = "active"

            # Synchronize Project model
            proj.git_repo_url = f"https://github.com/{clean_repo}"
            proj.git_branch = branch

        # 2. Normalize and Save Jira Project Key Mapping
        raw_jira_key = payload.jira_key
        if not raw_jira_key and payload.jira_project_keys:
            raw_jira_key = payload.jira_project_keys[0]
        if not raw_jira_key and payload.provider == "atlassian":
            raw_jira_key = payload.external_id or (payload.selected_resources[0] if payload.selected_resources else None)
        elif not raw_jira_key and payload.external_id and "/" not in str(payload.external_id):
            raw_jira_key = payload.external_id

        if raw_jira_key:
            clean_key = str(raw_jira_key).strip().upper()
            atl_server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "atlassian").first()
            atl_server_id = atl_server.id if atl_server else "atlassian-mcp-server"
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
                    server_id=atl_server_id,
                    provider="atlassian",
                    external_id=clean_key,
                )
                db.add(atl_mapping)

            atl_mapping.server_id = atl_server_id
            atl_mapping.external_id = clean_key
            atl_mapping.selected_resources = [clean_key]
            atl_mapping.status = "active"

            # Synchronize Project model
            proj.jira_project_key = clean_key

        db.commit()

        audit_logger.log_event(
            action="PROJECT_MCP_MAPPING_UPDATED",
            status="SUCCESS",
            details={
                "project_id": project_id,
                "project_name": proj.name,
                "git_repo_url": proj.git_repo_url,
                "git_branch": proj.git_branch,
                "jira_project_key": proj.jira_project_key,
            },
        )

        return {
            "status": "success",
            "project_id": project_id,
            "project_name": proj.name,
            "git_repo_url": proj.git_repo_url,
            "git_branch": proj.git_branch,
            "jira_project_key": proj.jira_project_key,
            "is_integrated": bool(proj.git_repo_url or proj.jira_project_key),
            "message": f"Successfully integrated {proj.name} with GitHub ({proj.git_repo_url or 'None'}) and Jira ({proj.jira_project_key or 'None'}).",
        }


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
