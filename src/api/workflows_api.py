"""
Testing Lifecycle Workflows API Endpoints.
"""

from typing import Dict, Any
import json
import asyncio
import threading
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
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
        from src.core.security.sanitizer import prompt_sanitizer
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        pdf_bytes = reporting_agent.export_pdf(report)
        safe_name = prompt_sanitizer.sanitize_filename(report.project_name)
        filename = f"{safe_name}_QA_Report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/report/csv")
def download_csv_report(project_id: str):
    """Downloads report metrics as CSV."""
    try:
        from src.core.security.sanitizer import prompt_sanitizer
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        csv_text = reporting_agent.export_csv(report)
        safe_name = prompt_sanitizer.sanitize_filename(report.project_name)
        filename = f"{safe_name}_Metrics.csv"
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/stream")
async def stream_testing_workflow(project_id: str, db: Session = Depends(get_db)):
    """Server-Sent Events (SSE) stream yielding real-time execution events for each agent node."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_text = project.description or "User Authentication and Checkout Payment Flow"
    initial_state = {
        "thread_id": f"thread_{project.id}",
        "project_id": project.id,
        "workflow_id": f"wf_{project.id}",
        "raw_input_text": raw_text,
        "source_type": "manual",
        "framework": project.framework or "playwright",
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

    agent_meta = {
        "requirement_analysis": {"name": "Requirements Analyst", "step": 1, "total": 6, "desc": "Analyzing repository and generating structured requirements..."},
        "scenario_generation": {"name": "Test Scenario Generator", "step": 2, "total": 6, "desc": "Synthesizing functional and security test scenarios..."},
        "test_case_design": {"name": "Test Case Designer", "step": 3, "total": 6, "desc": "Formulating detailed step-by-step test cases..."},
        "test_automation": {"name": "Automation Engineer", "step": 4, "total": 6, "desc": "Generating Playwright/Selenium test automation scripts..."},
        "test_execution": {"name": "Execution & Bug Hunter", "step": 5, "total": 6, "desc": "Executing test suite in isolated process sandbox..."},
        "orchestration_reporting": {"name": "Reporting & Quality Advisor", "step": 6, "total": 6, "desc": "Calculating quality readiness score and compiling report..."},
    }

    async def event_generator():
        yield f"data: {json.dumps({'event': 'workflow_started', 'project_id': project.id, 'project_name': project.name, 'message': 'LangGraph 6-agent autonomous workflow started.'})}\n\n"
        
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def producer():
            try:
                for chunk in testing_graph.stream(initial_state, stream_mode="updates"):
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))

        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        while True:
            msg_type, payload = await queue.get()
            if msg_type == "chunk":
                node_name = list(payload.keys())[0] if isinstance(payload, dict) else str(payload)
                meta = agent_meta.get(node_name, {"name": node_name, "step": 0, "total": 6, "desc": "Processing..."})
                yield f"data: {json.dumps({'event': 'agent_completed', 'node': node_name, 'agent': meta['name'], 'step': meta['step'], 'total_steps': meta['total'], 'details': meta['desc']})}\n\n"
            elif msg_type == "done":
                yield f"data: {json.dumps({'event': 'workflow_completed', 'status': 'success', 'message': 'All 6 agents successfully executed.'})}\n\n"
                break
            elif msg_type == "error":
                yield f"data: {json.dumps({'event': 'workflow_error', 'error': payload})}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
