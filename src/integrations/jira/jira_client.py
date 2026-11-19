"""
Jira REST API Client and MCP Integration.
Extracts user stories, acceptance criteria, business rules, and linked issues.
Strictly read-only by default to prevent unintended modifications to client projects.
"""

from typing import List, Dict, Any, Optional
import httpx
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger("jira_client")


class JiraClient:
    def __init__(self, host_url: str, email: str, api_token: str):
        self.host_url = host_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = (self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> Dict[str, Any]:
        """Validates Jira connection and retrieves current user profile."""
        url = f"{self.host_url}/rest/api/3/myself"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, auth=self.auth, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "connected": True,
                        "display_name": data.get("displayName", "Authorized User"),
                        "email": data.get("emailAddress", self.email),
                        "time_zone": data.get("timeZone", "UTC"),
                    }
                else:
                    return {
                        "connected": False,
                        "error": f"Jira returned HTTP {response.status_code}: {response.text}",
                    }
        except Exception as e:
            logger.error(f"Jira connection failed: {e}")
            return {"connected": False, "error": str(e)}

    def get_projects(self) -> List[Dict[str, Any]]:
        """Retrieves list of accessible Jira projects."""
        url = f"{self.host_url}/rest/api/3/project"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, auth=self.auth, headers=self.headers)
                if response.status_code == 200:
                    projects = response.json()
                    return [
                        {
                            "key": p.get("key"),
                            "name": p.get("name"),
                            "id": p.get("id"),
                            "project_type": p.get("projectTypeKey"),
                        }
                        for p in projects
                    ]
                else:
                    raise IntegrationError(f"Failed to fetch Jira projects: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Jira projects: {e}")
            raise IntegrationError(f"Could not connect to Jira projects: {e}")

    def get_issues(self, project_key: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Fetches issues for a given project with custom field resolution."""
        url = f"{self.host_url}/rest/api/3/search"
        jql = f"project = {project_key} ORDER BY created DESC"
        params = {"jql": jql, "maxResults": max_results}

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, auth=self.auth, headers=self.headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    issues = []
                    for item in data.get("issues", []):
                        fields = item.get("fields", {})
                        # Extract description safely (handles Atlassian Document Format ADF or plain text)
                        desc_text = self._extract_description(fields.get("description"))

                        # Detect acceptance criteria from custom fields or description
                        acceptance_criteria = self._extract_acceptance_criteria(fields, desc_text)

                        issues.append({
                            "key": item.get("key"),
                            "summary": fields.get("summary", ""),
                            "description": desc_text,
                            "acceptance_criteria": acceptance_criteria,
                            "issue_type": fields.get("issuetype", {}).get("name", "Story"),
                            "priority": fields.get("priority", {}).get("name", "Medium"),
                            "status": fields.get("status", {}).get("name", "To Do"),
                            "labels": fields.get("labels", []),
                        })
                    return issues
                else:
                    raise IntegrationError(f"Failed to fetch Jira issues for {project_key}: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {e}")
            raise IntegrationError(f"Could not retrieve issues for Jira project {project_key}: {e}")

    def _extract_description(self, raw_desc: Any) -> str:
        if not raw_desc:
            return ""
        if isinstance(raw_desc, str):
            return raw_desc
        # Extract from ADF structure
        if isinstance(raw_desc, dict) and "content" in raw_desc:
            texts = []
            for node in raw_desc.get("content", []):
                for sub in node.get("content", []):
                    if sub.get("type") == "text":
                        texts.append(sub.get("text", ""))
            return " ".join(texts)
        return str(raw_desc)

    def _extract_acceptance_criteria(self, fields: Dict[str, Any], description: str) -> List[str]:
        # Search for custom field containing 'acceptance'
        for k, v in fields.items():
            if "acceptance" in k.lower() and v:
                if isinstance(v, list):
                    return [str(item) for item in v]
                return [line.strip("- *") for line in str(v).split("\n") if line.strip()]

        # Parse from description if marked with 'Acceptance Criteria:'
        criteria = []
        if "acceptance criteria" in description.lower():
            parts = description.split("Acceptance Criteria:")
            if len(parts) > 1:
                lines = parts[1].split("\n")
                for line in lines:
                    line = line.strip(" -*#\r")
                    if line:
                        criteria.append(line)
        return criteria if criteria else ["Verify all happy path and error conditions satisfy business requirements."]

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
    ) -> Dict[str, Any]:
        """Creates a defect or story in the target Jira project."""
        url = f"{self.host_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, auth=self.auth, headers=self.headers, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    logger.info(f"Created Jira issue: {data.get('key')}")
                    return {"success": True, "issue_key": data.get("key"), "id": data.get("id")}
                else:
                    return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return {"success": False, "error": str(e)}
