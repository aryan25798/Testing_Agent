"""
Agent-Facing MCP Integration Adapter.
Provides high-level, typed methods for LangGraph agents to access GitHub repositories
and Jira projects strictly via the MCP Tool Registry.
Direct REST API fallbacks are explicitly forbidden.
"""

import json
from typing import List, Dict, Any, Optional
from src.integrations.mcp.tool_registry import tool_registry
from src.database.session import SessionLocal
from src.models.entities import ProjectIntegrationMapping, Project
from src.core.security.sanitizer import prompt_sanitizer
from src.core.logging import get_logger

logger = get_logger("mcp_agent_client")


class MCPAgentClient:
    """
    Adapter used by LangGraph testing agents to query GitHub and Jira via MCP tools.
    Enforces project boundaries and wraps untrusted output in safety boundaries.
    """

    @staticmethod
    def _get_project_repo_slug(project_id: str) -> Optional[str]:
        """Resolves the owner/repo mapped to the internal project."""
        with SessionLocal() as db:
            mapping = (
                db.query(ProjectIntegrationMapping)
                .filter(
                    ProjectIntegrationMapping.project_id == project_id,
                    ProjectIntegrationMapping.provider == "github",
                    ProjectIntegrationMapping.status == "active",
                )
                .first()
            )
            if mapping and mapping.selected_resources:
                return mapping.selected_resources[0]
            if mapping and mapping.external_id:
                return mapping.external_id

            # Fallback to project git_repo_url if mapping row not yet created
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj and proj.git_repo_url:
                clean = proj.git_repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
                return clean
        return None

    @staticmethod
    def _get_project_jira_key(project_id: str) -> Optional[str]:
        """Resolves the Jira project key mapped to the internal project."""
        with SessionLocal() as db:
            mapping = (
                db.query(ProjectIntegrationMapping)
                .filter(
                    ProjectIntegrationMapping.project_id == project_id,
                    ProjectIntegrationMapping.provider == "atlassian",
                    ProjectIntegrationMapping.status == "active",
                )
                .first()
            )
            if mapping and mapping.selected_resources:
                return mapping.selected_resources[0]

            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj and proj.jira_project_key:
                return proj.jira_project_key
        return None

    @classmethod
    async def get_jira_issues(
        cls,
        project_id: str,
        issue_key: Optional[str] = None,
        max_results: int = 15,
        agent_id: str = "agent_1_requirement_analysis",
    ) -> List[Dict[str, Any]]:
        """
        Retrieves Jira user stories and acceptance criteria via Atlassian MCP tool.
        """
        jira_project = cls._get_project_jira_key(project_id) or "TEST"

        try:
            # Check available Atlassian tools dynamically
            tools = tool_registry.get_registered_tools("atlassian")
            tool_names = [t["tool_name"] for t in tools]

            if issue_key:
                target_tool = "jira_get_issue" if "jira_get_issue" in tool_names else tool_names[0] if tool_names else None
                if not target_tool:
                    logger.info("Atlassian MCP has no discovered tools. Continuing in requirements-only mode.")
                    return []
                args = {"issue_key": issue_key}
                raw_res = await tool_registry.invoke_tool_safely(
                    project_id=project_id,
                    provider="atlassian",
                    agent_id=agent_id,
                    tool_name=target_tool,
                    arguments=args,
                )
                return [{"key": issue_key, "raw_content": raw_res}]
            else:
                if "jira_search" in tool_names:
                    target_tool = "jira_search"
                    args = {"jql": f"project = {jira_project} ORDER BY created DESC", "limit": max_results}
                elif "jira_get_project_issues" in tool_names:
                    target_tool = "jira_get_project_issues"
                    args = {"project_key": jira_project, "limit": max_results}
                elif "jira_search_for_issues_using_jql" in tool_names:
                    target_tool = "jira_search_for_issues_using_jql"
                    args = {"jql": f"project = {jira_project} ORDER BY created DESC"}
                else:
                    logger.info(f"No Jira issue search tool found among discovered tools: {tool_names}. Continuing in requirements-only mode.")
                    return []

                raw_res = await tool_registry.invoke_tool_safely(
                    project_id=project_id,
                    provider="atlassian",
                    agent_id=agent_id,
                    tool_name=target_tool,
                    arguments=args,
                )
                return [{"jql": f"project = {jira_project}", "raw_content": raw_res, "tool_used": target_tool}]

        except Exception as e:
            logger.warning(f"MCP Jira issue retrieval failed: {e}")
            return []

    @classmethod
    async def get_github_file(
        cls,
        project_id: str,
        file_path: str = "README.md",
        branch: str = "main",
        agent_id: str = "agent_1_requirement_analysis",
    ) -> str:
        """
        Reads a specific file from the connected GitHub repository using MCP get_file_contents tool.
        """
        repo_slug = cls._get_project_repo_slug(project_id)
        if not repo_slug:
            logger.info(f"Project '{project_id}' has no connected GitHub repository mapped. Proceeding with user-provided requirements.")
            return ""

        parts = repo_slug.split("/")
        owner = parts[0]
        repo = parts[1] if len(parts) > 1 else parts[0]

        args = {"owner": owner, "repo": repo, "path": file_path, "ref": branch}

        try:
            raw_res = await tool_registry.invoke_tool_safely(
                project_id=project_id,
                provider="github",
                agent_id=agent_id,
                tool_name="get_file_contents",
                arguments=args,
            )
        except Exception as e:
            logger.info(f"GitHub MCP file read '{file_path}' not available: {e}")
            return ""

        try:
            parsed = json.loads(raw_res)
            if isinstance(parsed, dict) and "content" in parsed and isinstance(parsed["content"], str):
                return parsed["content"]
        except Exception:
            pass
        return raw_res

    @classmethod
    async def list_github_directory(
        cls,
        project_id: str,
        path: str = "",
        branch: str = "main",
        agent_id: str = "agent_4_test_automation",
    ) -> str:
        """
        Lists directory contents to inspect test frameworks and source structure using MCP get_file_contents.
        """
        return await cls.get_github_file(
            project_id=project_id, file_path=path, branch=branch, agent_id=agent_id
        )


mcp_agent_client = MCPAgentClient()
