"""
Integrations API Endpoints for Jira, Git, and Document Uploads.
Secured with AES-256-GCM vault integration, sanitized file uploads,
and audit logging.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field
from src.integrations.jira.jira_client import JiraClient
from src.integrations.git.git_client import GitClient
from src.integrations.files.parser import DocumentParser
from src.core.security.secrets_manager import secrets_manager
from src.core.security.audit_logger import audit_logger
from src.core.security.sanitizer import prompt_sanitizer

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class JiraCredentialsRequest(BaseModel):
    host_url: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)
    api_token: Optional[str] = Field(default=None, max_length=255)
    project_key: Optional[str] = Field(default=None, max_length=100)


class GitCredentialsRequest(BaseModel):
    provider: str = Field(default="github", max_length=50)
    host_url: str = Field(default="https://api.github.com", max_length=255)
    token: Optional[str] = Field(default=None, max_length=255)
    repo_full_name: Optional[str] = Field(default=None, max_length=255)
    branch: str = Field(default="main", max_length=100)


def _resolve_jira_token(token: Optional[str]) -> str:
    clean = token.strip() if token else None
    if not clean:
        clean = secrets_manager.get_secret("jira")
    if clean and token:
        secrets_manager.store_secret("jira", clean)
    return clean or ""


def _resolve_git_token(token: Optional[str]) -> Optional[str]:
    clean = token.strip() if token else None
    if not clean:
        clean = secrets_manager.get_secret("github")
    if clean and token:
        secrets_manager.store_secret("github", clean)
    return clean


@router.post("/jira/test")
def test_jira_connection(payload: JiraCredentialsRequest):
    token = _resolve_jira_token(payload.api_token)
    if not token:
        raise HTTPException(status_code=400, detail="Jira API token is required.")
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=token)
    res = client.test_connection()
    audit_logger.log_event(
        action="JIRA_CONNECTION_TEST",
        status="SUCCESS" if res.get("connected") else "FAILED",
        details={"host_url": payload.host_url, "email": payload.email},
    )
    return res


@router.post("/jira/projects")
def list_jira_projects(payload: JiraCredentialsRequest):
    token = _resolve_jira_token(payload.api_token)
    if not token:
        raise HTTPException(status_code=400, detail="Jira API token is required.")
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=token)
    return client.get_projects()


@router.post("/jira/issues")
def list_jira_issues(payload: JiraCredentialsRequest):
    if not payload.project_key:
        raise HTTPException(status_code=400, detail="project_key is required")
    token = _resolve_jira_token(payload.api_token)
    if not token:
        raise HTTPException(status_code=400, detail="Jira API token is required.")
    client = JiraClient(host_url=payload.host_url, email=payload.email, api_token=token)
    return client.get_issues(project_key=payload.project_key)


@router.post("/git/test")
def test_git_connection(payload: GitCredentialsRequest):
    token = _resolve_git_token(payload.token)
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=token)
    res = client.test_connection()
    audit_logger.log_event(
        action="GIT_CONNECTION_TEST",
        status="SUCCESS" if res.get("connected") else "FAILED",
        details={"provider": payload.provider, "host_url": payload.host_url},
    )
    return res


@router.post("/git/repositories")
def list_git_repositories(payload: GitCredentialsRequest):
    token = _resolve_git_token(payload.token)
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=token)
    return client.list_repositories()


@router.post("/git/inspect")
def inspect_git_repository(payload: GitCredentialsRequest):
    if not payload.repo_full_name:
        raise HTTPException(status_code=400, detail="repo_full_name is required")
    token = _resolve_git_token(payload.token)
    client = GitClient(provider=payload.provider, host_url=payload.host_url, token=token)
    return client.inspect_repository_structure(repo_full_name=payload.repo_full_name, branch=payload.branch)


@router.post("/upload")
async def upload_requirement_file(file: UploadFile = File(...)):
    """Uploads and parses a PDF, DOCX, XLSX, CSV, or TXT file into clean text."""
    safe_filename = prompt_sanitizer.sanitize_filename(file.filename or "upload.txt")
    content = await file.read()
    try:
        extracted_text = DocumentParser.parse_file(file_content=content, filename=safe_filename)
        audit_logger.log_event(
            action="FILE_UPLOAD_PARSED",
            status="SUCCESS",
            details={"filename": safe_filename, "size_bytes": len(content)},
        )
        return {
            "filename": safe_filename,
            "size_bytes": len(content),
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
        }
    except Exception as e:
        safe_msg = prompt_sanitizer.redact_secrets(str(e))
        audit_logger.log_event(
            action="FILE_UPLOAD_FAILED",
            status="ERROR",
            details={"filename": safe_filename, "error": safe_msg},
            severity="WARNING",
        )
        raise HTTPException(status_code=400, detail=safe_msg)
