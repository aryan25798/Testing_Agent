"""
Integrations API Endpoints for Jira, Git, and Document Uploads.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from src.integrations.jira.jira_client import JiraClient
from src.integrations.git.git_client import GitClient
from src.integrations.files.parser import DocumentParser

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class JiraCredentialsRequest(BaseModel):
    host_url: str
    email: str
    api_token: str
    project_key: Optional[str] = None


class GitCredentialsRequest(BaseModel):
    provider: str = "github"
    host_url: str = "https://api.github.com"
    token: Optional[str] = None
    repo_full_name: Optional[str] = None
    branch: str = "main"


@router.post("/jira/test")
def test_jira_connection(payload: JiraCredentialsRequest):
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=payload.api_token)
    return client.test_connection()


@router.post("/jira/projects")
def list_jira_projects(payload: JiraCredentialsRequest):
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=payload.api_token)
    return client.get_projects()


@router.post("/jira/issues")
def list_jira_issues(payload: JiraCredentialsRequest):
    if not payload.project_key:
        raise HTTPException(status_code=400, detail="project_key is required")
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=payload.api_token)
    return client.get_issues(project_key=payload.project_key)


@router.post("/git/test")
def test_git_connection(payload: GitCredentialsRequest):
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=payload.token)
    return client.test_connection()


@router.post("/git/repositories")
def list_git_repositories(payload: GitCredentialsRequest):
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=payload.token)
    return client.list_repositories()


@router.post("/git/inspect")
def inspect_git_repository(payload: GitCredentialsRequest):
    if not payload.repo_full_name:
        raise HTTPException(status_code=400, detail="repo_full_name is required")
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=payload.token)
    return client.inspect_repository_structure(repo_full_name=payload.repo_full_name, branch=payload.branch)


@router.post("/upload")
async def upload_requirement_file(file: UploadFile = File(...)):
    """Uploads and parses a PDF, DOCX, XLSX, CSV, or TXT file into clean text."""
    content = await file.read()
    try:
        extracted_text = DocumentParser.parse_file(file_content=content, filename=file.filename)
        return {
            "filename": file.filename,
            "size_bytes": len(content),
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
