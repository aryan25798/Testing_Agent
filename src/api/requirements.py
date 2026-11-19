"""
Requirements Management API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import Requirement, Project
from src.schemas.dtos import RequirementCreate, RequirementRead

router = APIRouter(prefix="/requirements", tags=["Requirements"])


@router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    req = Requirement(
        project_id=payload.project_id,
        requirement_key=payload.requirement_key,
        source_type=payload.source_type,
        title=payload.title,
        description=payload.description,
        business_objective=payload.business_objective,
        functional_requirements=payload.functional_requirements,
        non_functional_requirements=payload.non_functional_requirements,
        acceptance_criteria=payload.acceptance_criteria,
        business_rules=payload.business_rules,
        dependencies=payload.dependencies,
        missing_information=payload.missing_information,
        clarification_questions=payload.clarification_questions,
        risk_level=payload.risk_level,
        priority=payload.priority,
        testability_status=payload.testability_status,
        is_approved=payload.is_approved,
        approval_notes=payload.approval_notes,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/project/{project_id}", response_model=List[RequirementRead])
def list_requirements_by_project(project_id: str, db: Session = Depends(get_db)):
    return db.query(Requirement).filter(Requirement.project_id == project_id).order_by(Requirement.created_at.asc()).all()


@router.post("/{req_id}/approve", response_model=RequirementRead)
def approve_requirement(req_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    req.is_approved = True
    db.commit()
    db.refresh(req)
    return req


@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_requirement(req_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(req)
    db.commit()
    return None
