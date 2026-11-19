"""
Test Scenario Management API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import TestScenario, Project, Requirement
from src.schemas.dtos import TestScenarioCreate, TestScenarioRead

router = APIRouter(prefix="/scenarios", tags=["Test Scenarios"])


@router.post("", response_model=TestScenarioRead, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: TestScenarioCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scen = TestScenario(
        project_id=payload.project_id,
        requirement_id=payload.requirement_id,
        scenario_key=payload.scenario_key,
        title=payload.title,
        description=payload.description,
        test_type=payload.test_type,
        preconditions=payload.preconditions,
        test_objective=payload.test_objective,
        priority=payload.priority,
        risk=payload.risk,
        expected_outcome=payload.expected_outcome,
        automation_suitability=payload.automation_suitability,
        is_approved=payload.is_approved,
    )
    db.add(scen)
    db.commit()
    db.refresh(scen)
    return scen


@router.get("/project/{project_id}", response_model=List[TestScenarioRead])
def list_scenarios_by_project(project_id: str, db: Session = Depends(get_db)):
    return db.query(TestScenario).filter(TestScenario.project_id == project_id).order_by(TestScenario.created_at.asc()).all()


@router.post("/{scenario_id}/approve", response_model=TestScenarioRead)
def approve_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scen = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scen.is_approved = True
    db.commit()
    db.refresh(scen)
    return scen


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scen = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scen)
    db.commit()
    return None
