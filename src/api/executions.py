"""
Test Execution API Endpoints.
"""

import math
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import TestExecution, TestExecutionResult, Project
from src.schemas.dtos import (
    TestExecutionCreate,
    TestExecutionRead,
    BulkDeleteRequest,
    BulkDeleteResponse,
    PaginatedExecutionsResponse,
)
from src.core.reporting.junit_exporter import generate_junit_xml

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("/project/{project_id}", response_model=Union[PaginatedExecutionsResponse, List[TestExecutionRead]])
def list_project_executions(
    project_id: str,
    page: Optional[int] = Query(None, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None),
    runner_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(TestExecution).filter(TestExecution.project_id == project_id)

    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            (TestExecution.execution_key.ilike(s)) | (TestExecution.base_url.ilike(s))
        )

    if runner_type and runner_type.strip():
        query = query.filter(TestExecution.runner_type == runner_type.strip().lower())

    if status_filter == "passed":
        query = query.filter(TestExecution.failed_tests == 0)
    elif status_filter == "failed":
        query = query.filter(TestExecution.failed_tests > 0)

    query = query.order_by(TestExecution.created_at.desc())

    if page is not None:
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaginatedExecutionsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    return query.all()


@router.post("/bulk-delete", response_model=BulkDeleteResponse, status_code=status.HTTP_200_OK)
def bulk_delete_executions(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
    deleted_ids = []
    failed_ids = []

    for exec_id in payload.ids:
        execution = db.query(TestExecution).filter(TestExecution.id == exec_id).first()
        if not execution:
            failed_ids.append(exec_id)
            continue

        db.query(TestExecutionResult).filter(TestExecutionResult.execution_id == exec_id).delete(synchronize_session=False)
        db.delete(execution)
        deleted_ids.append(exec_id)

    db.commit()
    return BulkDeleteResponse(
        deleted_count=len(deleted_ids),
        deleted_ids=deleted_ids,
        failed_ids=failed_ids,
        message=f"Successfully deleted {len(deleted_ids)} execution record(s).",
    )


@router.get("/{execution_id}", response_model=TestExecutionRead)
def get_execution_details(execution_id: str, db: Session = Depends(get_db)):

    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution record not found")
    return execution


@router.get("/{execution_id}/export-junit")
def export_junit_xml(execution_id: str, db: Session = Depends(get_db)):
    """Exports test execution results as standard JUnit XML for CI/CD integration."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution record not found")
    
    xml_content = generate_junit_xml(execution)
    safe_filename = f"junit-{execution.execution_key}.xml"
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
    )
