"""
Test Case Management API Endpoints.
"""

import math
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import TestCase, Project, TestExecutionResult, AutomationScript
from src.schemas.dtos import (
    TestCaseCreate,
    TestCaseRead,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkApproveRequest,
    BulkApproveResponse,
    PaginatedTestCasesResponse,
)

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])


@router.post("", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
def create_test_case(payload: TestCaseCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tc = TestCase(
        project_id=payload.project_id,
        scenario_id=payload.scenario_id,
        requirement_id=payload.requirement_id,
        test_case_key=payload.test_case_key,
        title=payload.title,
        objective=payload.objective,
        test_type=payload.test_type,
        priority=payload.priority,
        preconditions=payload.preconditions,
        test_environment=payload.test_environment,
        test_data=payload.test_data,
        execution_steps=payload.execution_steps,
        expected_results=payload.expected_results,
        actual_results=payload.actual_results,
        status=payload.status,
        automation_suitability=payload.automation_suitability,
        tags=payload.tags,
        is_approved=payload.is_approved,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


@router.get("/project/{project_id}", response_model=Union[PaginatedTestCasesResponse, List[TestCaseRead]])
def list_test_cases(
    project_id: str,
    priority: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db),
):
    query = db.query(TestCase).filter(TestCase.project_id == project_id)

    if priority and priority.strip():
        query = query.filter(TestCase.priority == priority.strip())
    if test_type and test_type.strip():
        query = query.filter(TestCase.test_type == test_type.strip())
    if is_approved is not None:
        query = query.filter(TestCase.is_approved == is_approved)
    if search and search.strip():
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            (TestCase.title.ilike(search_filter))
            | (TestCase.test_case_key.ilike(search_filter))
            | (TestCase.objective.ilike(search_filter))
        )

    # Safe sorting
    sort_attr = getattr(TestCase, sort_by, None)
    if sort_attr is None:
        sort_attr = TestCase.created_at
    if sort_order.lower() == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())

    if page is not None:
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaginatedTestCasesResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    return query.all()


@router.post("/bulk-delete", response_model=BulkDeleteResponse, status_code=status.HTTP_200_OK)
def bulk_delete_test_cases(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
    deleted_ids = []
    failed_ids = []

    # Disassociate foreign key references in execution results and automation scripts
    db.query(TestExecutionResult).filter(TestExecutionResult.test_case_id.in_(payload.ids)).update({TestExecutionResult.test_case_id: None}, synchronize_session=False)
    db.query(AutomationScript).filter(AutomationScript.test_case_id.in_(payload.ids)).update({AutomationScript.test_case_id: None}, synchronize_session=False)

    for case_id in payload.ids:
        tc = db.query(TestCase).filter(TestCase.id == case_id).first()
        if not tc:
            failed_ids.append(case_id)
            continue
        db.delete(tc)
        deleted_ids.append(case_id)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during test case deletion: {str(e)}",
        )

    return BulkDeleteResponse(
        deleted_count=len(deleted_ids),
        deleted_ids=deleted_ids,
        failed_ids=failed_ids,
        message=f"Successfully deleted {len(deleted_ids)} test case(s).",
    )


@router.post("/bulk-approve", response_model=BulkApproveResponse, status_code=status.HTTP_200_OK)
def bulk_approve_test_cases(payload: BulkApproveRequest, db: Session = Depends(get_db)):
    approved_ids = []

    for case_id in payload.ids:
        tc = db.query(TestCase).filter(TestCase.id == case_id).first()
        if tc and not tc.is_approved:
            tc.is_approved = True
            tc.status = "Approved"
            approved_ids.append(case_id)

    db.commit()
    return BulkApproveResponse(
        approved_count=len(approved_ids),
        approved_ids=approved_ids,
        message=f"Successfully approved {len(approved_ids)} test case(s).",
    )



@router.post("/{case_id}/approve", response_model=TestCaseRead)
def approve_test_case(case_id: str, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    tc.is_approved = True
    tc.status = "Approved"
    db.commit()
    db.refresh(tc)
    return tc


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(case_id: str, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.query(TestExecutionResult).filter(TestExecutionResult.test_case_id == case_id).update({TestExecutionResult.test_case_id: None}, synchronize_session=False)
    db.query(AutomationScript).filter(AutomationScript.test_case_id == case_id).update({AutomationScript.test_case_id: None}, synchronize_session=False)
    db.delete(tc)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during test case deletion: {str(e)}",
        )
    return None
