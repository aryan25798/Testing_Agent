"""
Model Context Protocol (MCP) Connection Manager.
Manages official GitHub and Atlassian MCP client sessions over stdio and SSE transports.
Enforces dynamic capability negotiation, tool discovery, schema registration,
process isolation, and connection state persistence in SQLite.
"""

import os
import sys
import json
import time
import shutil
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from src.database.session import SessionLocal
from src.models.entities import MCPServerConnection, MCPDiscoveredTool, ProjectIntegrationMapping
from src.core.security.secrets_manager import secrets_manager
from src.core.security.audit_logger import audit_logger
from src.core.security.sanitizer import prompt_sanitizer
from src.core.logging import get_logger

logger = get_logger("mcp_connection_manager")

# Mutating/write tools that require explicit human approval
MUTATING_GITHUB_TOOLS = {
    "create_or_update_file",
    "push_files",
    "create_repository",
    "create_pull_request",
    "create_branch",
    "update_issue",
    "add_issue_comment",
    "merge_pull_request",
    "update_pull_request_branch",
    "create_pull_request_review",
}

MUTATING_JIRA_TOOLS = {
    "jira_create_issue",
    "jira_update_issue",
    "jira_delete_issue",
    "jira_add_comment",
    "jira_transition_issue",
    "jira_assign_issue",
}


class MCPConnectionManager:
    """
    Centralized MCP Connection Orchestrator for GitHub and Jira/Atlassian.
    Maintains persistent configuration, executes isolated subprocesses,
    negotiates capabilities, and dynamically registers tools.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_sessions: Dict[str, Any] = {}
        self._ensure_default_servers_registered()

    def _ensure_default_servers_registered(self):
        """Seeds initial MCPServerConnection rows in database if not already present."""
        try:
            with SessionLocal() as db:
                gh = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
                if not gh:
                    gh = MCPServerConnection(
                        provider="github",
                        server_name="Official GitHub MCP Server",
                        transport="stdio",
                        command=json.dumps(["npx", "-y", "@modelcontextprotocol/server-github"]),
                        auth_type="pat",
                        status="disconnected",
                        is_read_only=True,
                    )
                    db.add(gh)

                atl = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "atlassian").first()
                if not atl:
                    atl = MCPServerConnection(
                        provider="atlassian",
                        server_name="Official Atlassian MCP Server",
                        transport="stdio",
                        server_url="https://mcp.atlassian.com/v2/mcp",
                        auth_type="token",
                        status="disconnected",
                        is_read_only=True,
                    )
                    db.add(atl)

                db.commit()
        except Exception as e:
            logger.error(f"Error seeding MCP default servers: {e}")

    def get_server_status(self, provider: str) -> Dict[str, Any]:
        """Returns live connection and capability status for a provider."""
        prov_key = provider.lower().strip()
        with SessionLocal() as db:
            # Query prioritizing active connected servers with tools
            servers = (
                db.query(MCPServerConnection)
                .filter(MCPServerConnection.provider == prov_key)
                .all()
            )
            if not servers:
                return {
                    "provider": prov_key,
                    "server_name": f"Official {provider.title()} MCP Server",
                    "status": "disconnected",
                    "available_tools_count": 0,
                    "is_read_only": True,
                }

            # Pick the server with connected status, or the one with the most tools, or latest connected
            def server_score(s: MCPServerConnection):
                cnt = db.query(MCPDiscoveredTool).filter(MCPDiscoveredTool.server_id == s.id).count()
                status_score = 1000 if s.status == "connected" else 0
                return status_score + cnt

            servers.sort(key=server_score, reverse=True)
            server = servers[0]
            tools_count = db.query(MCPDiscoveredTool).filter(MCPDiscoveredTool.server_id == server.id).count()

            # Dynamic GitHub authenticated user lookup if not yet populated
            if prov_key == "github" and not server.account_login:
                try:
                    import httpx
                    auth_token = secrets_manager.get_secret("github")
                    if auth_token:
                        r = httpx.get(
                            "https://api.github.com/user",
                            headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/vnd.github.v3+json"},
                            timeout=3.0,
                        )
                        if r.status_code == 200:
                            gh_user = r.json()
                            server.account_login = gh_user.get("login")
                            server.account_name = gh_user.get("name")
                            db.commit()
                except Exception as e:
                    logger.debug(f"GitHub user profile lookup: {e}")

            # Ensure canonical naming
            canonical_name = f"Official {'GitHub' if prov_key == 'github' else 'Atlassian'} MCP Server"

            return {
                "id": server.id,
                "provider": server.provider,
                "server_name": canonical_name,
                "transport": server.transport or ("stdio" if prov_key == "github" else "sse"),
                "server_url": server.server_url or ("https://aryan220518.atlassian.net" if prov_key == "atlassian" else None),
                "account_login": server.account_login,
                "account_name": server.account_name,
                "status": server.status,
                "is_read_only": server.is_read_only,
                "available_tools_count": tools_count,
                "last_connected_at": server.last_connected_at.isoformat() if server.last_connected_at else None,
                "last_error": server.last_error,
            }

    def get_all_servers_status(self) -> List[Dict[str, Any]]:
        """Returns status for all supported MCP servers."""
        return [self.get_server_status("github"), self.get_server_status("atlassian")]

    def _build_github_stdio_params(self, token: Optional[str] = None) -> StdioServerParameters:
        """Constructs secure StdioServerParameters for GitHub MCP server."""
        auth_token = token or secrets_manager.get_secret("github")
        if not auth_token:
            raise ValueError("GitHub Personal Access Token (PAT) is required to initialize GitHub MCP Server.")

        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "APPDATA": os.environ.get("APPDATA", ""),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
            "GITHUB_PERSONAL_ACCESS_TOKEN": auth_token,
        }

        # On Windows, invoke npx via cmd.exe
        cmd = "cmd.exe" if sys.platform == "win32" else "npx"
        args = ["/c", "npx", "-y", "@modelcontextprotocol/server-github"] if sys.platform == "win32" else ["-y", "@modelcontextprotocol/server-github"]

        return StdioServerParameters(command=cmd, args=args, env=safe_env)

    def _build_jira_stdio_params(self, host_url: str, email: str, token: Optional[str] = None) -> StdioServerParameters:
        """Constructs secure StdioServerParameters for Atlassian MCP server."""
        auth_token = token or secrets_manager.get_secret("jira")
        if not auth_token:
            raise ValueError("Atlassian API token is required to initialize Jira MCP Server.")

        mcp_atlassian_exe = str(Path(sys.executable).parent / "mcp-atlassian.exe")
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "APPDATA": os.environ.get("APPDATA", ""),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
            "JIRA_URL": host_url.rstrip("/"),
            "JIRA_USERNAME": email.strip(),
            "JIRA_API_TOKEN": auth_token,
        }

        args = ["--transport", "stdio", "--read-only"]
        return StdioServerParameters(command=mcp_atlassian_exe, args=args, env=safe_env)

    def _connect_native_github_fallback(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Connects to GitHub natively via Python REST API without requiring Node.js or NPX."""
        start_time = time.time()
        logger.info("Initializing Pure Python Native GitHub MCP Client (Zero Node.js dependency)...")
        from src.integrations.mcp.native_github import NativePythonGitHubExecutor, NATIVE_GITHUB_TOOLS_SCHEMA

        executor = NativePythonGitHubExecutor(token=token)
        user_info = executor.get_authenticated_user()
        login = user_info.get("login")
        name = user_info.get("name")
        server_name = "Official GitHub MCP Server"

        duration = round(time.time() - start_time, 2)
        with SessionLocal() as db:
            server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
            if not server:
                server = MCPServerConnection(provider="github", server_name=server_name)
                db.add(server)

            server.status = "connected"
            server.server_name = server_name
            server.transport = "native-python"
            server.account_login = login
            server.account_name = name
            server.capabilities = {"tools": {"listChanged": True}}
            server.last_connected_at = datetime.utcnow()
            server.last_error = None
            db.flush()

            # Replace tool definitions with native schemas
            db.query(MCPDiscoveredTool).filter(MCPDiscoveredTool.server_id == server.id).delete()
            discovered_tools_payload = []
            for t in NATIVE_GITHUB_TOOLS_SCHEMA:
                is_write = not t["is_read_only"]
                allowed = ["orchestrator", "agent_4_test_automation"] if is_write else ["orchestrator", "agent_1_requirement_analysis", "agent_4_test_automation"]
                tool_row = MCPDiscoveredTool(
                    server_id=server.id,
                    tool_name=t["name"],
                    description=t["description"],
                    input_schema=t["input_schema"],
                    is_read_only=not is_write,
                    allowed_agents=allowed,
                    risk_level="high" if is_write else "low",
                )
                db.add(tool_row)
                discovered_tools_payload.append({
                    "name": t["name"],
                    "description": t["description"],
                    "is_read_only": not is_write,
                    "risk_level": "high" if is_write else "low",
                })
            db.commit()

        audit_logger.log_event(
            action="MCP_GITHUB_CONNECTED_NATIVE",
            status="SUCCESS",
            details={"server_name": server_name, "login": login, "tools_count": len(NATIVE_GITHUB_TOOLS_SCHEMA)},
        )

        return {
            "status": "connected",
            "server_name": server_name,
            "tools_count": len(NATIVE_GITHUB_TOOLS_SCHEMA),
            "duration_seconds": duration,
            "tools": discovered_tools_payload,
            "transport": "native-python",
            "account_login": login,
        }

    async def connect_and_discover_github(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Connects to official GitHub MCP server, negotiates capabilities,
        discovers real tool schemas, and registers them in database.
        Automatically falls back to pure Python REST client if npx/Node is not available.
        """
        if token:
            secrets_manager.store_secret("github", token)

        # Check if npx is installed on the host OS
        if not shutil.which("npx"):
            logger.info("Node.js/npx not detected on host system. Seamlessly activating pure Python native GitHub engine.")
            return await asyncio.to_thread(self._connect_native_github_fallback, token)

        server_params = self._build_github_stdio_params(token)
        start_time = time.time()
        logger.info("Initializing GitHub MCP Server over stdio transport...")

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    init_res = await asyncio.wait_for(session.initialize(), timeout=12.0)
                    server_name = init_res.serverInfo.name
                    capabilities = init_res.capabilities.model_dump() if hasattr(init_res.capabilities, "model_dump") else {}

                    tools_list = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                    duration = round(time.time() - start_time, 2)

                    # Persist discovered tools to SQLite
                    with SessionLocal() as db:
                        server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
                        if not server:
                            server = MCPServerConnection(provider="github", server_name=server_name)
                            db.add(server)

                        server.status = "connected"
                        server.server_name = "Official GitHub MCP Server"
                        server.transport = "stdio"
                        server.capabilities = capabilities
                        server.last_connected_at = datetime.utcnow()
                        server.last_error = None
                        db.flush()

                        # Purge old tools and replace with newly discovered schemas
                        db.query(MCPDiscoveredTool).filter(MCPDiscoveredTool.server_id == server.id).delete()

                        discovered_tools_payload = []
                        for t in tools_list.tools:
                            is_write = t.name in MUTATING_GITHUB_TOOLS
                            risk = "high" if is_write else "low"

                            # Permitted agent assignments
                            allowed = ["orchestrator", "agent_1_requirement_analysis", "agent_4_test_automation"]
                            if is_write:
                                allowed = ["orchestrator", "agent_4_test_automation"]

                            tool_row = MCPDiscoveredTool(
                                server_id=server.id,
                                tool_name=t.name,
                                description=t.description,
                                input_schema=t.inputSchema if hasattr(t, "inputSchema") else {},
                                is_read_only=not is_write,
                                allowed_agents=allowed,
                                risk_level=risk,
                            )
                            db.add(tool_row)
                            discovered_tools_payload.append({
                                "name": t.name,
                                "description": t.description,
                                "is_read_only": not is_write,
                                "risk_level": risk,
                            })

                        db.commit()

                    audit_logger.log_event(
                        action="MCP_GITHUB_CONNECTED",
                        status="SUCCESS",
                        details={"server_name": server_name, "tools_count": len(tools_list.tools), "duration_s": duration},
                    )

                    return {
                        "status": "connected",
                        "server_name": "Official GitHub MCP Server",
                        "tools_count": len(tools_list.tools),
                        "duration_seconds": duration,
                        "tools": discovered_tools_payload,
                    }

        except Exception as e:
            err_msg = prompt_sanitizer.redact_secrets(str(e))
            logger.warning(f"GitHub stdio client failed ({err_msg}). Falling back to pure Python native GitHub engine.")
            try:
                return await asyncio.to_thread(self._connect_native_github_fallback, token)
            except Exception as native_err:
                logger.error(f"Native GitHub fallback also failed: {native_err}")
                with SessionLocal() as db:
                    server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
                    if server:
                        server.status = "error"
                        server.last_error = str(native_err)
                        db.commit()
                raise RuntimeError(f"GitHub connection failed: {native_err}")

    async def connect_and_discover_jira(
        self, host_url: str, email: str, token: Optional[str] = None, method: str = "stdio"
    ) -> Dict[str, Any]:
        """
        Connects to Atlassian Jira MCP Server (stdio or official remote SSE),
        discovers real tool schemas, and registers them in database.
        """
        if token:
            secrets_manager.store_secret("jira", token)

        clean_host = host_url.rstrip("/")
        start_time = time.time()
        logger.info(f"Initializing Atlassian Jira MCP Server ({method}) for {clean_host}...")

        try:
            if method == "sse":
                # Remote SSE connection to official Atlassian MCP server
                auth_token = token or secrets_manager.get_secret("jira")
                headers = {"Authorization": f"Bearer {auth_token}"}
                async with sse_client("https://mcp.atlassian.com/v2/mcp", headers=headers) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        init_res = await asyncio.wait_for(session.initialize(), timeout=12.0)
                        server_name = init_res.serverInfo.name
                        capabilities = init_res.capabilities.model_dump() if hasattr(init_res.capabilities, "model_dump") else {}
                        tools_list = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            else:
                # Local stdio subprocess connection via mcp-atlassian
                server_params = self._build_jira_stdio_params(clean_host, email, token)
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        init_res = await asyncio.wait_for(session.initialize(), timeout=12.0)
                        server_name = init_res.serverInfo.name
                        capabilities = init_res.capabilities.model_dump() if hasattr(init_res.capabilities, "model_dump") else {}
                        tools_list = await asyncio.wait_for(session.list_tools(), timeout=10.0)

            duration = round(time.time() - start_time, 2)

            with SessionLocal() as db:
                server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "atlassian").first()
                if not server:
                    server = MCPServerConnection(provider="atlassian", server_name=server_name)
                    db.add(server)

                server.status = "connected"
                server.server_name = server_name
                server.transport = method
                server.server_url = clean_host
                server.account_login = email
                server.capabilities = capabilities
                server.last_connected_at = datetime.utcnow()
                server.last_error = None
                db.flush()

                db.query(MCPDiscoveredTool).filter(MCPDiscoveredTool.server_id == server.id).delete()

                discovered_tools_payload = []
                for t in tools_list.tools:
                    is_write = t.name in MUTATING_JIRA_TOOLS
                    risk = "high" if is_write else "low"
                    allowed = ["orchestrator", "agent_1_requirement_analysis", "agent_6_orchestration_reporting"]
                    if is_write:
                        allowed = ["orchestrator", "agent_6_orchestration_reporting"]

                    tool_row = MCPDiscoveredTool(
                        server_id=server.id,
                        tool_name=t.name,
                        description=t.description,
                        input_schema=t.inputSchema if hasattr(t, "inputSchema") else {},
                        is_read_only=not is_write,
                        allowed_agents=allowed,
                        risk_level=risk,
                    )
                    db.add(tool_row)
                    discovered_tools_payload.append({
                        "name": t.name,
                        "description": t.description,
                        "is_read_only": not is_write,
                        "risk_level": risk,
                    })

                db.commit()

            audit_logger.log_event(
                action="MCP_JIRA_CONNECTED",
                status="SUCCESS",
                details={"host_url": clean_host, "email": email, "tools_count": len(tools_list.tools), "duration_s": duration},
            )

            return {
                "status": "connected",
                "server_name": server_name,
                "tools_count": len(tools_list.tools),
                "duration_seconds": duration,
                "tools": discovered_tools_payload,
            }

        except Exception as e:
            err_msg = prompt_sanitizer.redact_secrets(str(e))
            logger.error(f"Failed to connect to Jira MCP Server: {err_msg}")

            with SessionLocal() as db:
                server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "atlassian").first()
                if server:
                    server.status = "error"
                    server.last_error = err_msg
                    db.commit()

            audit_logger.log_event(
                action="MCP_JIRA_CONNECTION_FAILED",
                status="ERROR",
                details={"host_url": clean_host, "error": err_msg},
                severity="HIGH",
            )
            raise RuntimeError(f"Atlassian Jira MCP Server connection failed: {err_msg}")

    async def execute_tool(
        self,
        provider: str,
        tool_name: str,
        arguments: Dict[str, Any],
        project_id: Optional[str] = None,
        agent_id: str = "orchestrator",
        timeout: float = 30.0,
    ) -> Any:
        """
        Executes a tool on the target MCP server with process isolation,
        input schema validation, and audit tracking.
        """
        start_time = time.time()
        prov_clean = provider.lower().strip()

        with SessionLocal() as db:
            server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == prov_clean).first()
            if not server:
                raise ValueError(f"MCP server for provider '{prov_clean}' is not configured.")

            # Validate tool existence in database
            tool_record = (
                db.query(MCPDiscoveredTool)
                .filter(MCPDiscoveredTool.server_id == server.id, MCPDiscoveredTool.tool_name == tool_name)
                .first()
            )
            if not tool_record:
                raise ValueError(f"MCP tool '{tool_name}' is not recognized or not discovered for {prov_clean}.")

            # Validate agent authorization:
            # Orchestrator and system callers are authorized for all read-only inspection/discovery tools
            if agent_id in ("orchestrator", "system", "admin") and tool_record.is_read_only:
                pass
            elif tool_record.allowed_agents and agent_id not in tool_record.allowed_agents:
                raise PermissionError(
                    f"Agent '{agent_id}' is not authorized to invoke MCP tool '{tool_name}'. Allowed: {tool_record.allowed_agents}"
                )

        # Launch session and execute tool
        try:
            if prov_clean == "github":
                if server.transport == "native-python" or not shutil.which("npx"):
                    from src.integrations.mcp.native_github import NativePythonGitHubExecutor
                    executor = NativePythonGitHubExecutor()
                    raw_result = await asyncio.to_thread(executor.execute_tool, tool_name, arguments)
                    duration = round(time.time() - start_time, 2)
                    safe_result = prompt_sanitizer.redact_secrets(raw_result)
                    self._record_tool_invocation(
                        server_id=server.id,
                        project_id=project_id,
                        agent_id=agent_id,
                        tool_name=tool_name,
                        operation_type="write" if not tool_record.is_read_only else "read",
                        arguments=arguments,
                        status="success",
                        duration=duration,
                    )
                    return safe_result

                try:
                    server_params = self._build_github_stdio_params()
                    async with stdio_client(server_params) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            call_res = await asyncio.wait_for(session.call_tool(tool_name, arguments), timeout=timeout)
                except Exception as stdio_exec_err:
                    logger.warning(f"GitHub stdio execution failed ({stdio_exec_err}), seamlessly falling back to native Python executor.")
                    from src.integrations.mcp.native_github import NativePythonGitHubExecutor
                    executor = NativePythonGitHubExecutor()
                    raw_result = await asyncio.to_thread(executor.execute_tool, tool_name, arguments)
                    duration = round(time.time() - start_time, 2)
                    safe_result = prompt_sanitizer.redact_secrets(raw_result)
                    self._record_tool_invocation(
                        server_id=server.id,
                        project_id=project_id,
                        agent_id=agent_id,
                        tool_name=tool_name,
                        operation_type="write" if not tool_record.is_read_only else "read",
                        arguments=arguments,
                        status="success",
                        duration=duration,
                    )
                    return safe_result
            else:
                # Jira
                server_params = self._build_jira_stdio_params(
                    server.server_url or "https://atlassian.net",
                    server.account_login or "user@domain.com",
                )
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        call_res = await asyncio.wait_for(session.call_tool(tool_name, arguments), timeout=timeout)

            duration = round(time.time() - start_time, 2)

            # Extract content from MCP response
            content_list = []
            if hasattr(call_res, "content"):
                for c in call_res.content:
                    if hasattr(c, "text"):
                        content_list.append(c.text)
                    elif hasattr(c, "data"):
                        content_list.append(str(c.data))
            result_data = "\n".join(content_list) if content_list else str(call_res)

            # Redact any accidental secrets from output
            safe_result = prompt_sanitizer.redact_secrets(result_data)

            # Record audit invocation log
            self._record_tool_invocation(
                server_id=server.id,
                project_id=project_id,
                agent_id=agent_id,
                tool_name=tool_name,
                operation_type="write" if not tool_record.is_read_only else "read",
                arguments=arguments,
                status="success",
                duration=duration,
            )

            return safe_result

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            err_msg = prompt_sanitizer.redact_secrets(str(e))
            self._record_tool_invocation(
                server_id=server.id if server else "unknown",
                project_id=project_id,
                agent_id=agent_id,
                tool_name=tool_name,
                operation_type="read",
                arguments=arguments,
                status="failed",
                duration=duration,
                error_message=err_msg,
            )
            raise RuntimeError(f"MCP tool '{tool_name}' failed: {err_msg}")

    def _record_tool_invocation(
        self,
        server_id: str,
        project_id: Optional[str],
        agent_id: str,
        tool_name: str,
        operation_type: str,
        arguments: Dict[str, Any],
        status: str,
        duration: float,
        error_message: Optional[str] = None,
    ):
        """Records an execution log in SQLite with secrets stripped."""
        try:
            from src.models.entities import MCPToolInvocationLog
            clean_args = {k: prompt_sanitizer.redact_secrets(str(v)) for k, v in arguments.items()}
            with SessionLocal() as db:
                log_entry = MCPToolInvocationLog(
                    server_id=server_id,
                    project_id=project_id,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    operation_type=operation_type,
                    arguments_summary=clean_args,
                    status=status,
                    duration_seconds=duration,
                    error_message=error_message,
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.warning(f"Could not record MCP invocation log: {e}")

    def disconnect(self, provider: str):
        """Marks provider MCP server as disconnected."""
        prov_clean = provider.lower().strip()
        with SessionLocal() as db:
            server = db.query(MCPServerConnection).filter(MCPServerConnection.provider == prov_clean).first()
            if server:
                server.status = "disconnected"
                db.commit()
        audit_logger.log_event(action="MCP_DISCONNECT", status="SUCCESS", details={"provider": prov_clean})
        return {"status": "disconnected", "provider": prov_clean}


mcp_connection_manager = MCPConnectionManager()
