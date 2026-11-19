"""
Test Case Management API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import TestCase, Project
from src.schemas.dtos import TestCaseCreate, TestCaseRead

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


@router.get("/project/{project_id}", response_model=List[TestCaseRead])
def list_test_cases(
    project_id: str,
    priority: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(TestCase).filter(TestCase.project_id == project_id)

    if priority:
        query = query.filter(TestCase.priority == priority)
    if test_type:
        query = query.filter(TestCase.test_type == test_type)
    if is_approved is not None:
        query = query.filter(TestCase.is_approved == is_approved)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (TestCase.title.ilike(search_filter))
            | (TestCase.test_case_key.ilike(search_filter))
            | (TestCase.objective.ilike(search_filter))
        )

    return query.order_by(TestCase.created_at.asc()).all()


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
    db.delete(tc)
    db.commit()
    return None
