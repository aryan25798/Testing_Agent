"""
Project Management API Endpoints.
"""

import math
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
    TestExecutionResult,
    ApprovalRequest,
    AgentExecution,
    ProjectIntegrationMapping,
    MCPApprovalRequest,
)
from src.core.logging import get_logger
from src.schemas.dtos import (
    ProjectCreate,
    ProjectRead,
    BulkDeleteRequest,
    BulkDeleteResponse,
    PaginatedProjectsResponse,
)
from src.core.workflow_runner import workflow_runner

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = get_logger("projects_api")


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=payload.name,
        description=payload.description,
        framework=payload.framework,
        jira_project_key=payload.jira_project_key,
        git_repo_url=payload.git_repo_url,
        git_branch=payload.git_branch,
        base_url=payload.base_url,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=Union[PaginatedProjectsResponse, List[ProjectRead]])
def list_projects(
    page: Optional[int] = Query(None, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Project)

    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            (Project.name.ilike(s)) | (Project.description.ilike(s)) | (Project.base_url.ilike(s))
        )

    if framework and framework.strip():
        query = query.filter(Project.framework == framework.strip().lower())

    # Safe sorting
    sort_attr = getattr(Project, sort_by, None)
    if sort_attr is None:
        sort_attr = Project.created_at
    if sort_order.lower() == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    if page is not None:
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaginatedProjectsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    return query.all()


@router.post("/bulk-delete", response_model=BulkDeleteResponse, status_code=status.HTTP_200_OK)
def bulk_delete_projects(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
    active_workflows = workflow_runner.list_active()
    active_proj_ids = {w["project_id"] for w in active_workflows}

    deleted_ids = []
    failed_ids = []

    for proj_id in payload.ids:
        if proj_id in active_proj_ids:
            failed_ids.append(proj_id)
            continue

        project = db.query(Project).filter(Project.id == proj_id).first()
        if not project:
            failed_ids.append(proj_id)
            continue

        # Cascading transactional cleanup
        exec_ids = [e.id for e in db.query(TestExecution).filter(TestExecution.project_id == proj_id).all()]
        if exec_ids:
            db.query(TestExecutionResult).filter(TestExecutionResult.execution_id.in_(exec_ids)).delete(synchronize_session=False)
        db.query(TestExecution).filter(TestExecution.project_id == proj_id).delete(synchronize_session=False)
        db.query(AutomationScript).filter(AutomationScript.project_id == proj_id).delete(synchronize_session=False)
        db.query(TestCase).filter(TestCase.project_id == proj_id).delete(synchronize_session=False)
        db.query(TestScenario).filter(TestScenario.project_id == proj_id).delete(synchronize_session=False)
        db.query(Requirement).filter(Requirement.project_id == proj_id).delete(synchronize_session=False)
        db.query(ApprovalRequest).filter(ApprovalRequest.project_id == proj_id).delete(synchronize_session=False)
        db.query(MCPApprovalRequest).filter(MCPApprovalRequest.project_id == proj_id).delete(synchronize_session=False)
        db.query(ProjectIntegrationMapping).filter(ProjectIntegrationMapping.project_id == proj_id).delete(synchronize_session=False)
        db.query(AgentExecution).filter(AgentExecution.project_id == proj_id).delete(synchronize_session=False)

        db.delete(project)
        deleted_ids.append(proj_id)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit bulk project deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during project deletion: {str(e)}",
        )

    msg = f"Successfully deleted {len(deleted_ids)} project(s)."
    if failed_ids:
        msg += f" {len(failed_ids)} project(s) could not be deleted (not found or active workflows running)."

    return BulkDeleteResponse(
        deleted_count=len(deleted_ids),
        deleted_ids=deleted_ids,
        failed_ids=failed_ids,
        message=msg,
    )


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, payload: ProjectCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = payload.name
    project.description = payload.description
    project.framework = payload.framework
    project.jira_project_key = payload.jira_project_key
    project.git_repo_url = payload.git_repo_url
    project.git_branch = payload.git_branch
    project.base_url = payload.base_url
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Safety check: prevent deleting project if an automated workflow is actively running
    active_workflows = workflow_runner.list_active()
    active_for_project = [w for w in active_workflows if w["project_id"] == project_id]
    if active_for_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete project '{project.name}' because an automated testing workflow is actively running. Please cancel the workflow first or wait for completion.",
        )

    # Cascading cleanup
    exec_ids = [e.id for e in db.query(TestExecution).filter(TestExecution.project_id == project_id).all()]
    if exec_ids:
        db.query(TestExecutionResult).filter(TestExecutionResult.execution_id.in_(exec_ids)).delete(synchronize_session=False)
    db.query(TestExecution).filter(TestExecution.project_id == project_id).delete(synchronize_session=False)
    db.query(AutomationScript).filter(AutomationScript.project_id == project_id).delete(synchronize_session=False)
    db.query(TestCase).filter(TestCase.project_id == project_id).delete(synchronize_session=False)
    db.query(TestScenario).filter(TestScenario.project_id == project_id).delete(synchronize_session=False)
    db.query(Requirement).filter(Requirement.project_id == project_id).delete(synchronize_session=False)
    db.query(ApprovalRequest).filter(ApprovalRequest.project_id == project_id).delete(synchronize_session=False)
    db.query(MCPApprovalRequest).filter(MCPApprovalRequest.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectIntegrationMapping).filter(ProjectIntegrationMapping.project_id == project_id).delete(synchronize_session=False)
    db.query(AgentExecution).filter(AgentExecution.project_id == project_id).delete(synchronize_session=False)

    db.delete(project)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit project deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during project deletion: {str(e)}",
        )
    return None



@router.get("/{project_id}/dashboard", response_model=Dict[str, Any])
def get_project_dashboard(project_id: str, db: Session = Depends(get_db)):
    """
    Returns aggregated dashboard metrics matching the enterprise dashboard UI:
    - 4 KPI cards: Test Suites, Schedules, Run History (passed/failed), Success Rate %
    - Distribution: Passed, Failed, Pending
    - Execution Trends
    - Test Suites Overview
    - Recent Activity stream
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    requirements_count = db.query(Requirement).filter(Requirement.project_id == project_id).count()
    scenarios_count = db.query(TestScenario).filter(TestScenario.project_id == project_id).count()
    cases_count = db.query(TestCase).filter(TestCase.project_id == project_id).count()
    automation_count = db.query(AutomationScript).filter(AutomationScript.project_id == project_id).count()

    executions = db.query(TestExecution).filter(TestExecution.project_id == project_id).order_by(TestExecution.created_at.desc()).all()
    
    total_runs = len(executions)
    total_passed = sum(e.passed_tests for e in executions)
    total_failed = sum(e.failed_tests for e in executions)
    total_skipped = sum(e.skipped_tests for e in executions)
    total_tests_run = total_passed + total_failed + total_skipped

    success_rate = round((total_passed / total_tests_run * 100), 1) if total_tests_run > 0 else 0.0

    # Build suites overview
    # A test suite can group test scenarios and test cases
    scenarios = db.query(TestScenario).filter(TestScenario.project_id == project_id).all()
    test_suites_data = []
    if scenarios:
        for s in scenarios[:5]:
            c_count = db.query(TestCase).filter(TestCase.scenario_id == s.id).count()
            test_suites_data.append({
                "suite_name": s.title,
                "scenarios": 1,
                "cases": c_count if c_count > 0 else 1,
                "status": "Active" if s.is_approved else "Pending Review"
            })
    else:
        test_suites_data = []

    # Build recent activity
    activity = []
    for e in executions[:5]:
        status_text = "Passed" if e.failed_tests == 0 and e.passed_tests > 0 else "Failed"
        activity.append({
            "type": "run",
            "title": f"Execution {e.execution_key} {status_text}",
            "description": f"{e.passed_tests} passed, {e.failed_tests} failed via {e.runner_type}",
            "timestamp": e.created_at.strftime("%b %d, %H:%M")
        })

    if not activity:
        activity = [
            {"type": "info", "title": "Project Initialized", "description": f"Framework: {project.framework}", "timestamp": "Just now"},
        ]

    return {
        "project_id": project.id,
        "project_name": project.name,
        "framework": project.framework,
        "metrics": {
            "test_suites": max(1, scenarios_count),
            "total_scenarios": scenarios_count,
            "schedules": 0,
            "run_history": total_runs,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "pending_tests": cases_count - automation_count if cases_count > automation_count else 0,
            "success_rate": success_rate,
            "total_requirements": requirements_count,
            "total_test_cases": cases_count,
            "automated_tests": automation_count,
        },
        "test_results_overview": {
            "total": total_tests_run if total_tests_run > 0 else cases_count,
            "passed": total_passed,
            "failed": total_failed,
            "pending": max(0, cases_count - total_tests_run),
        },
        "test_suites_overview": test_suites_data,
        "recent_activity": activity,
    }
