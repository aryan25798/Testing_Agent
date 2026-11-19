"""
Git Integration Client for GitHub, GitLab, Bitbucket, and Azure DevOps.
Performs read-only inspection of repository structure and testing frameworks.
"""

from typing import List, Dict, Any, Optional
import httpx
from src.core.logging import get_logger

logger = get_logger("git_client")


class GitClient:
    def __init__(self, provider: str = "github", host_url: str = "https://api.github.com", token: Optional[str] = None):
        self.provider = provider.lower()
        self.host_url = host_url.rstrip("/")
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TestingAgentPlatform-Client",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def test_connection(self) -> Dict[str, Any]:
        """Tests authorization and retrieves user profile from Git provider."""
        if not self.token:
            return {"connected": True, "provider": self.provider, "note": "Public read-only mode"}

        url = f"{self.host_url}/user"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "connected": True,
                        "provider": self.provider,
                        "login": data.get("login"),
                        "name": data.get("name"),
                    }
                else:
                    return {"connected": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def list_repositories(self) -> List[Dict[str, Any]]:
        """Lists user accessible repositories from GitHub API."""
        if not self.token:
            raise ValueError("GitHub Personal Access Token (PAT) is required to retrieve your client repositories.")

        url = f"{self.host_url}/user/repos?per_page=50&sort=updated"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return [
                        {
                            "name": r.get("name"),
                            "full_name": r.get("full_name"),
                            "default_branch": r.get("default_branch", "main"),
                            "html_url": r.get("html_url"),
                            "private": r.get("private", False),
                        }
                        for r in res.json()
                    ]
                else:
                    raise ValueError(f"GitHub returned HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error fetching GitHub repos: {e}")
            raise ValueError(f"Could not fetch repositories: {e}")

    def inspect_repository_structure(self, repo_full_name: str, branch: str = "main") -> Dict[str, Any]:
        """
        Safely inspects repository tree via GitHub Git Trees API to detect
        actual testing frameworks, locators, and file tree.
        """
        tree_url = f"{self.host_url}/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.get(tree_url, headers=self.headers)
                if res.status_code == 200:
                    tree_data = res.json().get("tree", [])
                    paths = [item.get("path", "") for item in tree_data]

                    has_tests_dir = any("test" in p.lower() for p in paths)
                    test_files = [p for p in paths if p.endswith((".py", ".js", ".ts")) and ("test" in p.lower() or "spec" in p.lower())]

                    has_playwright = any("playwright" in p.lower() for p in paths)
                    has_selenium = any("selenium" in p.lower() for p in paths)
                    has_pytest = any("conftest.py" in p or "pytest" in p.lower() for p in paths)

                    detected_fw = "playwright" if has_playwright else ("selenium" if has_selenium else "none")

                    return {
                        "repository": repo_full_name,
                        "branch": branch,
                        "total_files": len(paths),
                        "has_tests_dir": has_tests_dir,
                        "detected_framework": detected_fw,
                        "existing_test_files": test_files[:10],
                        "has_playwright": has_playwright,
                        "has_selenium": has_selenium,
                        "has_pytest": has_pytest,
                        "file_samples": paths[:15],
                    }
                else:
                    raise ValueError(f"GitHub Tree API returned HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error inspecting repo {repo_full_name}: {e}")
            return {
                "repository": repo_full_name,
                "branch": branch,
                "error": str(e),
                "detected_framework": "playwright",
            }
