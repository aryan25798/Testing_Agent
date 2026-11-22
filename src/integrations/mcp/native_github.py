"""
Native Pure-Python GitHub MCP Engine.
Allows the Testing Agent Platform to discover and execute GitHub tools without requiring Node.js or NPX.
Uses direct GitHub REST v3 API calls with AES-256 encrypted Personal Access Tokens.
"""

import os
import json
import base64
import time
from typing import Dict, Any, List, Optional
import httpx
from src.core.security.secrets_manager import secrets_manager
from src.core.logging import get_logger

logger = get_logger("native_github_mcp")

NATIVE_GITHUB_TOOLS_SCHEMA = [
    {
        "name": "get_file_contents",
        "description": "Reads raw contents of a specific file from a GitHub repository.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner / organization."},
                "repo": {"type": "string", "description": "Repository name."},
                "path": {"type": "string", "description": "Path to the file (e.g. README.md)."},
                "ref": {"type": "string", "description": "Branch, tag, or commit SHA (default 'main').", "default": "main"},
            },
            "required": ["owner", "repo", "path"],
        },
    },
    {
        "name": "list_directory",
        "description": "Lists directory files and structure in a repository path.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "path": {"type": "string", "default": ""},
                "ref": {"type": "string", "default": "main"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "get_repository",
        "description": "Retrieves metadata and default branch details for a GitHub repository.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "list_issues",
        "description": "Lists issues from a GitHub repository.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {"type": "string", "default": "open"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "get_issue",
        "description": "Retrieves a single issue by number.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "issue_number": {"type": "integer"},
            },
            "required": ["owner", "repo", "issue_number"],
        },
    },
    {
        "name": "list_pull_requests",
        "description": "Lists pull requests from a GitHub repository.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {"type": "string", "default": "open"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "list_commits",
        "description": "Lists recent commits from a GitHub repository.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "ref": {"type": "string", "default": "main"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "search_repositories",
        "description": "Searches GitHub repositories by query string.",
        "is_read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_issue",
        "description": "Creates a new issue in a GitHub repository.",
        "is_read_only": False,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["owner", "repo", "title"],
        },
    },
    {
        "name": "create_or_update_file",
        "description": "Creates or updates a file in a GitHub repository (requires approval).",
        "is_read_only": False,
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "message": {"type": "string"},
                "branch": {"type": "string", "default": "main"},
            },
            "required": ["owner", "repo", "path", "content", "message"],
        },
    },
]


class NativePythonGitHubExecutor:
    """Executes GitHub MCP tools natively over REST API when Node.js/npx is not installed."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or secrets_manager.get_secret("github") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TestingAgentPlatform-NativeMCP/1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def get_authenticated_user(self) -> Dict[str, Any]:
        """Fetches the authenticated user profile."""
        url = "https://api.github.com/user"
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            raise RuntimeError(f"GitHub user authorization failed: HTTP {res.status_code}")

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Executes the requested GitHub MCP tool and returns JSON string."""
        with httpx.Client(timeout=15.0) as client:
            if tool_name == "get_file_contents":
                owner = args["owner"]
                repo = args["repo"]
                path = args["path"].lstrip("/")
                ref = args.get("ref", "main")
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    content_b64 = data.get("content", "")
                    if content_b64:
                        decoded = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                        return json.dumps({"content": decoded, "path": path, "size": data.get("size")})
                    return json.dumps(data)
                elif res.status_code == 404:
                    raise FileNotFoundError(f"File '{path}' not found in {owner}/{repo} (branch: {ref}).")
                else:
                    raise RuntimeError(f"GitHub API Error: HTTP {res.status_code} - {res.text}")

            elif tool_name == "list_directory":
                owner = args["owner"]
                repo = args["repo"]
                path = args.get("path", "").lstrip("/")
                ref = args.get("ref", "main")
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    items = res.json()
                    if isinstance(items, list):
                        summary = [
                            {"name": i.get("name"), "path": i.get("path"), "type": i.get("type"), "size": i.get("size")}
                            for i in items
                        ]
                        return json.dumps({"directory": path, "items": summary})
                    return json.dumps(items)
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code} - {res.text}")

            elif tool_name == "get_repository":
                owner = args["owner"]
                repo = args["repo"]
                url = f"https://api.github.com/repos/{owner}/{repo}"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    return json.dumps({
                        "name": data.get("name"),
                        "full_name": data.get("full_name"),
                        "default_branch": data.get("default_branch"),
                        "description": data.get("description"),
                        "private": data.get("private"),
                        "html_url": data.get("html_url"),
                    })
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "list_issues":
                owner = args["owner"]
                repo = args["repo"]
                state = args.get("state", "open")
                url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&per_page=30"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    issues = [
                        {"number": i.get("number"), "title": i.get("title"), "state": i.get("state"), "user": i.get("user", {}).get("login")}
                        for i in res.json()
                    ]
                    return json.dumps(issues)
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "get_issue":
                owner = args["owner"]
                repo = args["repo"]
                num = args["issue_number"]
                url = f"https://api.github.com/repos/{owner}/{repo}/issues/{num}"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return json.dumps(res.json())
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "list_pull_requests":
                owner = args["owner"]
                repo = args["repo"]
                state = args.get("state", "open")
                url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}&per_page=20"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return json.dumps(res.json())
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "list_commits":
                owner = args["owner"]
                repo = args["repo"]
                ref = args.get("ref", "main")
                url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={ref}&per_page=20"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return json.dumps(res.json())
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "search_repositories":
                query = args["query"]
                url = f"https://api.github.com/search/repositories?q={query}&per_page=10"
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return json.dumps(res.json().get("items", []))
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code}")

            elif tool_name == "create_issue":
                owner = args["owner"]
                repo = args["repo"]
                payload = {"title": args["title"], "body": args.get("body", "")}
                url = f"https://api.github.com/repos/{owner}/{repo}/issues"
                res = client.post(url, headers=self.headers, json=payload)
                if res.status_code in (200, 201):
                    return json.dumps(res.json())
                raise RuntimeError(f"GitHub API Error: HTTP {res.status_code} - {res.text}")

            else:
                raise ValueError(f"Unknown or unsupported native GitHub tool: '{tool_name}'")
