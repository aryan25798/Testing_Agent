"""
Test Execution API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import TestExecution, TestExecutionResult, Project
from src.schemas.dtos import TestExecutionCreate, TestExecutionRead
from src.core.reporting.junit_exporter import generate_junit_xml

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("/project/{project_id}", response_model=List[TestExecutionRead])
def list_project_executions(project_id: str, db: Session = Depends(get_db)):
    return db.query(TestExecution).filter(TestExecution.project_id == project_id).order_by(TestExecution.created_at.desc()).all()


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
