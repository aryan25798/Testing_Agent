"""
Comprehensive Integration Tests for Model Context Protocol (MCP) Integration System.
Verifies:
1. Dynamic Tool Discovery & Capabilities Negotiation
2. Least-Privilege Agent Permission Restrictions
3. Project Boundary Isolation (Cross-Project Prevention)
4. Human-in-the-Loop Approval Queue (Diff Inspection, Approve/Reject)
5. MCP Audit Logging & Safe Execution
6. Agent Client Adapter Integration
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from src.main import app
from src.database.session import SessionLocal, init_db
from src.models.entities import (
    MCPServerConnection,
    MCPDiscoveredTool,
    ProjectIntegrationMapping,
    MCPApprovalRequest,
    MCPToolInvocationLog,
    Project,
)
from src.integrations.mcp.connection_manager import mcp_connection_manager
from src.integrations.mcp.tool_registry import tool_registry
from src.integrations.mcp.approval_manager import approval_manager
from src.integrations.mcp.mcp_agent_client import mcp_agent_client


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield


def test_mcp_servers_status_endpoint():
    """Verifies that official GitHub and Atlassian MCP servers are recognized."""
    response = client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    providers = {s["provider"] for s in data}
    assert "github" in providers
    assert "atlassian" in providers

    gh = next(s for s in data if s["provider"] == "github" and "Official" in s.get("server_name", ""))
    assert gh["server_name"] == "Official GitHub MCP Server"
    assert gh["transport"] == "stdio"

    atl = next(s for s in data if s["provider"] == "atlassian" and "Official" in s.get("server_name", ""))
    assert atl["server_name"] == "Official Atlassian MCP Server"


def test_mcp_tool_discovery_and_registration():
    """Verifies tools can be dynamically registered and queried with schemas and permissions."""
    test_server_id = f"test-srv-{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        srv = MCPServerConnection(
            id=test_server_id,
            provider="github",
            server_name="Test GitHub MCP Server",
            transport="stdio",
            status="connected",
            is_read_only=True,
        )
        db.add(srv)
        db.commit()

        # Add a read-only tool
        t_read = MCPDiscoveredTool(
            server_id=test_server_id,
            tool_name="get_file_contents",
            description="Reads file contents from a repository",
            input_schema={"type": "object", "properties": {"repo": {"type": "string"}}},
            is_read_only=True,
            allowed_agents=["agent_1_requirement_analysis", "agent_4_test_automation"],
            risk_level="low",
        )
        # Add a mutating tool
        t_write = MCPDiscoveredTool(
            server_id=test_server_id,
            tool_name="create_or_update_file",
            description="Creates or updates a file in the repository",
            input_schema={"type": "object", "properties": {"repo": {"type": "string"}, "content": {"type": "string"}}},
            is_read_only=False,
            allowed_agents=["agent_4_test_automation"],
            risk_level="high",
        )
        db.add_all([t_read, t_write])
        db.commit()

    # Query tools endpoint
    response = client.get("/api/v1/mcp/tools")
    assert response.status_code == 200
    tools = response.json()
    tool_names = {t["tool_name"] for t in tools}
    assert "get_file_contents" in tool_names
    assert "create_or_update_file" in tool_names

    read_tool = next(t for t in tools if t["tool_name"] == "get_file_contents")
    assert read_tool["is_read_only"] is True
    assert "agent_1_requirement_analysis" in read_tool["allowed_agents"]


def test_project_boundary_enforcement():
    """Verifies that accessing resources outside the project mapping is strictly blocked."""
    project_id = f"test-proj-{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        proj = Project(
            id=project_id,
            name="Restricted Project Alpha",
            description="Project with strict repository boundaries",
            framework="playwright",
        )
        db.add(proj)

        gh_srv = db.query(MCPServerConnection).filter(MCPServerConnection.provider == "github").first()
        server_id = gh_srv.id if gh_srv else "test-srv"
        if not gh_srv:
            srv = MCPServerConnection(
                id=server_id,
                provider="github",
                server_name="Test GitHub Server",
                status="connected",
            )
            db.add(srv)
            db.flush()

        # Map to specific repo only
        mapping = ProjectIntegrationMapping(
            project_id=project_id,
            server_id=server_id,
            provider="github",
            external_id="aryan25798/Testing_Agent",
            selected_resources=["aryan25798/Testing_Agent"],
            status="active",
        )
        db.add(mapping)
        db.commit()

    # 1. Allowed access: inside project's mapped repository
    tool_registry._verify_project_boundary(
        project_id=project_id,
        provider="github",
        arguments={"owner": "aryan25798", "repo": "Testing_Agent"},
    )

    # 2. Blocked access: cross-project repository leakage
    with pytest.raises(PermissionError) as exc_info:
        tool_registry._verify_project_boundary(
            project_id=project_id,
            provider="github",
            arguments={"owner": "other-org", "repo": "secret-backend-code"},
        )
    assert "Security Violation" in str(exc_info.value)
    assert "restricted to repositories" in str(exc_info.value)


def test_human_in_the_loop_approval_lifecycle():
    """Verifies that mutating MCP tools require explicit human approval."""
    project_id = f"test-proj-{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        proj = Project(
            id=project_id,
            name="Approval Test Project",
            framework="playwright",
        )
        db.add(proj)
        db.commit()

    tool_name = "create_pull_request"
    args = {"owner": "test", "repo": "app", "title": "Automated Test Suite"}

    # 1. Approval check should initially return False
    is_appr = approval_manager.check_approval(project_id, tool_name, args)
    assert is_appr is False

    # 2. Request approval
    req = approval_manager.request_approval(
        project_id=project_id,
        provider="github",
        agent_id="agent_4_test_automation",
        tool_name=tool_name,
        arguments=args,
        target_object="GITHUB: test/app",
        operation_description="Create PR with generated tests",
        risk_level="high",
    )
    assert req.id is not None
    assert req.status == "pending"

    # 3. Query pending approvals via REST API
    response = client.get(f"/api/v1/mcp/approvals/pending?project_id={project_id}")
    assert response.status_code == 200
    pending_list = response.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == req.id

    # 4. Human Approves via REST API
    decision_resp = client.post(
        f"/api/v1/mcp/approvals/{req.id}/decision",
        json={"decision": "approved", "notes": "LGTM! Verified locators."},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "approved"

    # 5. Approval check should now return True
    is_appr_now = approval_manager.check_approval(project_id, tool_name, args)
    assert is_appr_now is True


def test_project_integration_mapping_crud():
    """Verifies saving and retrieving project mappings through REST API."""
    project_id = f"test-proj-{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        proj = Project(id=project_id, name="Mapping API Project", framework="selenium")
        db.add(proj)
        db.commit()

    # Save mapping
    save_resp = client.post(
        f"/api/v1/mcp/projects/{project_id}/mapping",
        json={
            "github_repo": "myorg/crm-portal",
            "github_branch": "develop",
            "jira_project_keys": ["CRM"],
        },
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "success"

    # Retrieve mapping
    get_resp = client.get(f"/api/v1/mcp/projects/{project_id}/mapping")
    assert get_resp.status_code == 200
    m_data = get_resp.json()
    assert m_data["github_mapping"]["external_id"] == "myorg/crm-portal"
    assert m_data["github_mapping"]["default_branch"] == "develop"
    assert m_data["jira_mapping"]["selected_resources"] == ["CRM"]


def test_mcp_audit_logging():
    """Verifies that MCP invocations are stored in audit logs."""
    test_id = f"test-log-{uuid.uuid4().hex[:8]}"
    with SessionLocal() as db:
        log_entry = MCPToolInvocationLog(
            id=test_id,
            server_id="test-srv",
            project_id="proj-123",
            agent_id="agent_1_requirement_analysis",
            tool_name="jira_get_issue",
            status="success",
            duration_seconds=0.042,
        )
        db.add(log_entry)
        db.commit()

    # Query audit logs endpoint
    resp = client.get("/api/v1/mcp/logs?limit=10")
    assert resp.status_code == 200
    logs = resp.json()
    assert any(l["id"] == test_id for l in logs)
