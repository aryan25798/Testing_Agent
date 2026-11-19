"""
Testing Lifecycle Workflows API Endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import Project
from src.schemas.dtos import WorkflowStartRequest
from src.workflows.graph import testing_graph
from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent

router = APIRouter(prefix="/workflows", tags=["Workflows"])
reporting_agent = OrchestrationReportingAgent()


@router.post("/start")
def start_testing_workflow(payload: WorkflowStartRequest, db: Session = Depends(get_db)):
    """Triggers the complete 6-agent testing workflow via LangGraph."""
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_text = payload.requirements_text or project.description or "User Authentication and Checkout Payment Flow"

    initial_state = {
        "thread_id": f"thread_{project.id}",
        "project_id": project.id,
        "workflow_id": f"wf_{project.id}",
        "raw_input_text": raw_text,
        "source_type": payload.source_type,
        "framework": payload.framework or project.framework,
        "base_url": project.base_url or "http://127.0.0.1:8000",
        "requirements": [],
        "approved_requirements": [],
        "test_scenarios": [],
        "approved_scenarios": [],
        "test_cases": [],
        "approved_test_cases": [],
        "automation_scripts": [],
        "execution_results": [],
        "current_agent": "start",
        "step_count": 0,
        "errors": [],
        "approval_status": "Approved",
        "workflow_status": "InProgress",
        "consolidated_report": None,
    }

    try:
        final_state = testing_graph.invoke(initial_state)
        return {
            "status": "success",
            "project_id": project.id,
            "workflow_status": final_state.get("workflow_status"),
            "steps_completed": final_state.get("step_count"),
            "total_requirements": len(final_state.get("requirements", [])),
            "total_scenarios": len(final_state.get("test_scenarios", [])),
            "total_test_cases": len(final_state.get("test_cases", [])),
            "total_scripts": len(final_state.get("automation_scripts", [])),
            "total_executions": len(final_state.get("execution_results", [])),
            "report_summary": final_state.get("consolidated_report", {}).get("markdown_report", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {e}")


@router.get("/project/{project_id}/report")
def get_project_report(project_id: str):
    """Retrieves consolidated report data for a project."""
    try:
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/report/pdf")
def download_pdf_report(project_id: str):
    """Downloads formatted PDF report."""
    try:
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        pdf_bytes = reporting_agent.export_pdf(report)
        filename = f"{report.project_name.replace(' ', '_')}_QA_Report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/report/csv")
def download_csv_report(project_id: str):
    """Downloads report metrics as CSV."""
    try:
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        csv_text = reporting_agent.export_csv(report)
        filename = f"{report.project_name.replace(' ', '_')}_Metrics.csv"
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
