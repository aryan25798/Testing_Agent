"""
Git Integration Client for GitHub, GitLab, Bitbucket, and Azure DevOps.
Performs read-only inspection of repository structure and testing frameworks.
"""

from typing import List, Dict, Any, Optional
import base64
import httpx
from src.core.logging import get_logger

logger = get_logger("git_client")


class GitClient:
    def __init__(self, provider: str = "github", host_url: str = "https://api.github.com", token: Optional[str] = None):
        self.provider = provider.lower()
        self.host_url = host_url.rstrip("/")
        self.token = token.strip() if token else None
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TestingAgentPlatform-Client",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    @staticmethod
    def parse_repo_slug(url_or_slug: str) -> str:
        """Extracts 'owner/repo' from full GitHub URL, .git string, or raw slug."""
        clean = url_or_slug.strip().rstrip("/")
        if clean.endswith(".git"):
            clean = clean[:-4]
        if "github.com/" in clean:
            clean = clean.split("github.com/")[-1]
        # Remove any leading / or extra query params
        clean = clean.lstrip("/").split("?")[0]
        return clean

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
            raise ValueError("GitHub Personal Access Token (PAT) is required to retrieve your private/account repositories.")

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
        slug = self.parse_repo_slug(repo_full_name)
        tree_url = f"{self.host_url}/repos/{slug}/git/trees/{branch}?recursive=1"
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
                        "repository": slug,
                        "branch": branch,
                        "total_files": len(paths),
                        "has_tests_dir": has_tests_dir,
                        "detected_framework": detected_fw,
                        "existing_test_files": test_files[:10],
                        "has_playwright": has_playwright,
                        "has_selenium": has_selenium,
                        "has_pytest": has_pytest,
                        "file_samples": paths[:20],
                    }
                else:
                    raise ValueError(f"GitHub Tree API returned HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error inspecting repo {slug}: {e}")
            return {
                "repository": slug,
                "branch": branch,
                "error": str(e),
                "detected_framework": "playwright",
            }

    def get_file_content(self, repo_full_name: str, file_path: str = "README.md", branch: str = "main") -> Optional[str]:
        """Fetches raw text of a specific file from a GitHub repository."""
        slug = self.parse_repo_slug(repo_full_name)
        url = f"{self.host_url}/repos/{slug}/contents/{file_path}?ref={branch}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    content_b64 = data.get("content", "")
                    if content_b64:
                        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Could not read {file_path} from {slug}: {e}")
        return None

    def download_repo_archive(self, repo_full_name: str, branch: str = "main") -> bytes:
        """Downloads complete repository archive as zip bytes."""
        slug = self.parse_repo_slug(repo_full_name)
        url = f"{self.host_url}/repos/{slug}/zipball/{branch}"
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            res = client.get(url, headers=self.headers)
            if res.status_code == 200:
                return res.content
            raise ValueError(f"Failed to download repository zip from GitHub: HTTP {res.status_code}")
