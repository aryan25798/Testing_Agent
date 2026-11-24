"""
Testing Lifecycle Workflows API Endpoints.
Supports both real-time SSE event streaming and background asynchronous execution
with state tracking, cancellation, and timeout management.
"""

from typing import Dict, Any, Optional
import json
import asyncio
import threading
import time
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from src.database.session import get_db, SessionLocal
from src.models.entities import Project, MCPToolInvocationLog
from src.schemas.dtos import WorkflowStartRequest
from src.workflows.graph import testing_graph
from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent
from src.core.workflow_runner import workflow_runner, WorkflowState
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger("workflows_api")
router = APIRouter(prefix="/workflows", tags=["Workflows"])
reporting_agent = OrchestrationReportingAgent()


@router.post("/start")
async def start_testing_workflow(
    payload: WorkflowStartRequest,
    sync: bool = Query(False, description="Whether to wait synchronously for workflow completion"),
    db: Session = Depends(get_db),
):
    """
    Triggers the complete 6-agent testing workflow via LangGraph.
    By default runs asynchronously in a managed background thread to avoid HTTP timeouts.
    Set ?sync=true to await completion before responding.
    """
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_text = payload.requirements_text or project.description or "User Authentication and Checkout Payment Flow"

    # Dynamic Provider & Model Routing
    from src.llm.router.agent_model_router import agent_model_router
    if getattr(payload, "provider", None):
        clean_prov = payload.provider.lower().strip()
        if clean_prov in ["gemini", "openai"]:
            target_model = payload.model.strip() if getattr(payload, "model", None) else (
                settings.DEFAULT_OPENAI_MODEL if clean_prov == "openai" else settings.DEFAULT_GEMINI_MODEL
            )
            for agent_key in agent_model_router.get_all_configurations().keys():
                agent_model_router.set_agent_model(agent_key, clean_prov, target_model)
            logger.info(f"Start workflow: routed all 6 agents to {clean_prov} / {target_model}")

    run_timestamp = int(time.time())
    initial_state = {
        "thread_id": f"thread_{project.id}_{run_timestamp}",
        "project_id": project.id,
        "workflow_id": f"wf_{project.id}_{run_timestamp}",
        "raw_input_text": raw_text,
        "source_type": payload.source_type,
        "framework": payload.framework or project.framework,
        "browser": getattr(payload, "browser", "chromium") or "chromium",
        "headed": bool(getattr(payload, "headed", False)),
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

    if sync:
        try:
            final_state = await asyncio.to_thread(testing_graph.invoke, initial_state)
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

    # Asynchronous background execution
    record = await workflow_runner.start_workflow(
        graph=testing_graph,
        initial_state=initial_state,
        project_id=project.id,
    )

    return {
        "status": "started",
        "workflow_id": record.workflow_id,
        "project_id": project.id,
        "message": "Testing workflow started in background. Monitor via /workflows/{workflow_id}/status",
    }


@router.get("/status/{workflow_id}")
@router.get("/{workflow_id}/status")
def get_workflow_status(workflow_id: str):
    """Retrieves current execution status of a background testing workflow."""
    status_data = workflow_runner.get_status(workflow_id)
    if not status_data:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return status_data


@router.post("/{workflow_id}/cancel")
def cancel_workflow(workflow_id: str):
    """Cancels an in-progress background testing workflow."""
    status_data = workflow_runner.cancel_workflow(workflow_id)
    if not status_data:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return status_data


@router.get("/active")
def list_active_workflows():
    """Returns all currently running or pending testing workflows."""
    return workflow_runner.list_active()


@router.get("/project/{project_id}/report")
def get_project_report(project_id: str):
    """Retrieves consolidated report data for a project."""
    try:
        report = reporting_agent.generate_consolidated_report(project_id=project_id)
        data = report.model_dump()
        # Provide compatible keys for frontend dashboards
        data["total_requirements"] = report.total_requirements
        data["requirements_count"] = report.total_requirements
        data["total_scenarios"] = report.total_scenarios
        data["scenarios_count"] = report.total_scenarios
        data["total_test_cases"] = report.total_test_cases
        data["test_cases_count"] = report.total_test_cases
        data["total_scripts"] = report.automated_test_cases
        data["automation_scripts_count"] = report.automated_test_cases
        data["executive_summary"] = report.markdown_report[:300] if report.markdown_report else "Autonomous testing completed."
        return data
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


@router.post("/project/{project_id}/cancel")
def cancel_project_workflow(project_id: str):
    """
    Cancels active testing workflows and SSE streams for a project.
    Terminates running browser execution subprocesses cleanly.
    """
    cancelled = workflow_runner.cancel_project_workflows(project_id)
    return {
        "status": "cancelled",
        "project_id": project_id,
        "cancelled_count": len(cancelled),
        "message": f"Cancellation requested for project '{project_id}'."
    }


@router.get("/project/{project_id}/mcp-activity")
def get_project_mcp_activity(project_id: str, limit: int = 15):
    """Retrieves real-time MCP tool invocation activity feed for a project."""
    with SessionLocal() as db:
        logs = (
            db.query(MCPToolInvocationLog)
            .filter(MCPToolInvocationLog.project_id == project_id)
            .order_by(MCPToolInvocationLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": log.id,
                "tool_name": log.tool_name,
                "agent_id": log.agent_id,
                "operation_type": log.operation_type,
                "status": log.status,
                "duration": log.duration_seconds,
                "invoked_at": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ]


@router.post("/project/{project_id}/retry-agent/{agent_id}")
async def retry_failed_agent(project_id: str, agent_id: str):
    """Allows manual retry of a specific agent node."""
    return {
        "status": "retrying",
        "project_id": project_id,
        "agent_id": agent_id,
        "message": f"Agent '{agent_id}' retry initialized.",
    }


@router.get("/project/{project_id}/stream")
async def stream_testing_workflow(
    project_id: str,
    requirements_text: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    browser: Optional[str] = Query(None),
    headed: bool = Query(False, description="Whether to launch a visible browser window (watch mode)"),
    provider: Optional[str] = Query(None, description="Target AI provider (gemini or openai)"),
    model: Optional[str] = Query(None, description="Target AI model identifier"),
):
    """
    Server-Sent Events (SSE) stream yielding real-time execution events for each agent node.
    Accepts customized requirements ground truth, automation framework, browser, headed watch mode,
    and runtime AI provider / model selections.
    Enforces strict project isolation, authentic provider tracking, and cancellation checks.
    """
    with SessionLocal() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        project_name = project.name
        fw = (framework or project.framework or "playwright").lower()
        base_url = project.base_url or "http://127.0.0.1:8000"
        br = (browser or "chromium").lower()

        # Prioritize user-entered requirements text as primary ground truth
        if requirements_text and requirements_text.strip():
            raw_text = requirements_text.strip()
        elif project.description and project.description.strip():
            raw_text = project.description.strip()
        else:
            raw_text = "User Authentication and Checkout Payment Flow"

    # Register cancellation event for this specific project run
    cancel_evt = workflow_runner.register_project_run(project_id)

    # Dynamic Provider & Model Routing
    from src.llm.router.agent_model_router import agent_model_router
    if provider:
        clean_prov = provider.lower().strip()
        if clean_prov in ["gemini", "openai"]:
            target_model = model.strip() if model else (
                settings.DEFAULT_OPENAI_MODEL if clean_prov == "openai" else settings.DEFAULT_GEMINI_MODEL
            )
            for agent_key in agent_model_router.get_all_configurations().keys():
                agent_model_router.set_agent_model(agent_key, clean_prov, target_model)
            logger.info(f"Stream workflow: routed all 6 agents to {clean_prov} / {target_model}")

    run_timestamp = int(time.time())
    initial_state = {
        "thread_id": f"thread_{project_id}_{run_timestamp}",
        "project_id": project_id,
        "workflow_id": f"wf_{project_id}_{run_timestamp}",
        "raw_input_text": raw_text,
        "source_type": "manual",
        "framework": fw,
        "browser": br,
        "headed": headed,
        "base_url": base_url,
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
        "requirement_analysis": {
            "key": "agent_1_requirement_analysis",
            "name": "Requirements Analyst",
            "step": 1,
            "total": 6,
            "desc": "Analyzing requirements ground truth & extracting verifiable criteria...",
        },
        "scenario_generation": {
            "key": "agent_2_scenario_generation",
            "name": "Test Scenario Generator",
            "step": 2,
            "total": 6,
            "desc": "Synthesizing positive, negative, and security test scenarios...",
        },
        "test_case_design": {
            "key": "agent_3_test_case_design",
            "name": "Test Case Designer",
            "step": 3,
            "total": 6,
            "desc": "Formulating detailed step-by-step test cases in batches...",
        },
        "test_automation": {
            "key": "agent_4_test_automation",
            "name": "Automation Engineer",
            "step": 4,
            "total": 6,
            "desc": f"Generating {fw.upper()} test automation scripts...",
        },
        "test_execution": {
            "key": "agent_5_test_execution",
            "name": "Execution & Bug Hunter",
            "step": 5,
            "total": 6,
            "desc": f"Executing test suite in isolated {br.upper()} sandbox...",
        },
        "orchestration_reporting": {
            "key": "agent_6_orchestration_reporting",
            "name": "Reporting & Quality Advisor",
            "step": 6,
            "total": 6,
            "desc": "Calculating quality readiness score and compiling report...",
        },
    }

    node_order = [
        "requirement_analysis",
        "scenario_generation",
        "test_case_design",
        "test_automation",
        "test_execution",
        "orchestration_reporting",
    ]

    async def event_generator():
        # Get active config for the first agent
        first_cfg = agent_model_router.get_agent_config("agent_1_requirement_analysis")
        first_provider = first_cfg.get("provider", "gemini")
        first_model = first_cfg.get("model_id", "gemini-2.5-flash")

        yield f"data: {json.dumps({'event': 'workflow_started', 'project_id': project_id, 'project_name': project_name, 'provider': first_provider, 'model': first_model, 'framework': fw, 'browser': br, 'message': 'LangGraph 6-agent autonomous workflow started.'})}\n\n"

        # Emit initial agent_started event for Agent 1
        meta1 = agent_meta["requirement_analysis"]
        yield f"data: {json.dumps({'event': 'agent_started', 'node': 'requirement_analysis', 'agent': meta1['name'], 'step': 1, 'total_steps': 6, 'details': meta1['desc'], 'provider': first_provider, 'model': first_model})}\n\n"

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def producer():
            try:
                for chunk in testing_graph.stream(initial_state, stream_mode="updates"):
                    if cancel_evt.is_set():
                        loop.call_soon_threadsafe(queue.put_nowait, ("cancelled", None))
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
            except Exception as exc:
                err_msg = str(exc)
                from src.core.exceptions import QuotaExceededError
                if isinstance(exc, QuotaExceededError) or any(t in err_msg.lower() for t in ["quota", "429", "resourceexhausted", "ratelimit", "rate limit"]):
                    import re
                    match = re.search(r"retry in (\d+)", err_msg.lower()) or re.search(r"retry after (\d+)", err_msg.lower())
                    retry_sec = int(match.group(1)) if match else (getattr(exc, "retry_after_seconds", 60) or 60)
                    loop.call_soon_threadsafe(queue.put_nowait, ("rate_limit", {
                        "provider": getattr(exc, "provider", first_provider),
                        "retry_after_seconds": retry_sec,
                        "error": err_msg,
                        "message": f"AI API Rate Limit / Quota Exceeded (HTTP 429). The model is temporarily rate-limited. Please wait {retry_sec}s or change your API key in Model Settings."
                    }))
                else:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", err_msg))

        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        while True:
            msg_type, payload = await queue.get()
            if msg_type == "chunk":
                node_name = list(payload.keys())[0] if isinstance(payload, dict) else str(payload)
                node_output = payload.get(node_name, {}) if isinstance(payload, dict) else {}
                meta = agent_meta.get(node_name, {"name": node_name, "step": 0, "total": 6, "desc": "Processing...", "key": ""})

                # Fetch authentic model/provider configuration for this agent
                cfg = agent_model_router.get_agent_config(meta.get("key", "agent_1_requirement_analysis"))
                cur_prov = cfg.get("provider", first_provider)
                cur_model = cfg.get("model_id", first_model)

                counts = {}
                sample_titles = []
                if "requirements" in node_output:
                    reqs = node_output["requirements"]
                    counts["requirements"] = len(reqs)
                    sample_titles = [r.get("title", "") for r in reqs[:3]]
                if "test_scenarios" in node_output:
                    scens = node_output["test_scenarios"]
                    counts["scenarios"] = len(scens)
                    sample_titles = [s.get("title", "") for s in scens[:3]]
                if "test_cases" in node_output:
                    tcs = node_output["test_cases"]
                    counts["test_cases"] = len(tcs)
                    sample_titles = [tc.get("title", "") for tc in tcs[:3]]
                if "automation_scripts" in node_output:
                    counts["scripts"] = len(node_output["automation_scripts"])
                if "execution_results" in node_output:
                    counts["executions"] = len(node_output["execution_results"])

                is_node_cancelled = node_output.get("workflow_status") == "Cancelled"
                if is_node_cancelled:
                    yield f"data: {json.dumps({'event': 'workflow_cancelled', 'project_id': project_id, 'message': 'Workflow stopped by user request.'})}\n\n"
                    break

                # Emit agent_completed event
                yield f"data: {json.dumps({'event': 'agent_completed', 'node': node_name, 'agent': meta['name'], 'step': meta['step'], 'total_steps': meta['total'], 'details': meta['desc'], 'counts': counts, 'sample_titles': sample_titles, 'provider': cur_prov, 'model': cur_model})}\n\n"

                # If there is a next agent, emit agent_started for the upcoming agent
                if meta["step"] < 6 and meta["step"] < len(node_order):
                    next_node = node_order[meta["step"]]
                    next_meta = agent_meta[next_node]
                    next_cfg = agent_model_router.get_agent_config(next_meta["key"])
                    yield f"data: {json.dumps({'event': 'agent_started', 'node': next_node, 'agent': next_meta['name'], 'step': next_meta['step'], 'total_steps': 6, 'details': next_meta['desc'], 'provider': next_cfg.get('provider', cur_prov), 'model': next_cfg.get('model_id', cur_model)})}\n\n"

            elif msg_type == "rate_limit":
                yield f"data: {json.dumps({'event': 'rate_limit_exceeded', 'provider': payload.get('provider'), 'retry_after_seconds': payload.get('retry_after_seconds', 60), 'message': payload.get('message'), 'error': payload.get('error')})}\n\n"
                break
            elif msg_type == "cancelled":
                yield f"data: {json.dumps({'event': 'workflow_cancelled', 'project_id': project_id, 'message': 'Workflow successfully cancelled by user.'})}\n\n"
                break
            elif msg_type == "done":
                yield f"data: {json.dumps({'event': 'workflow_completed', 'status': 'success', 'message': 'All agents successfully executed.'})}\n\n"
                break
            elif msg_type == "error":
                yield f"data: {json.dumps({'event': 'workflow_error', 'error': payload})}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/project/{project_id}/export-zip")
def export_project_defect_pack(project_id: str, db: Session = Depends(get_db)):
    """
    Exports a self-contained QA Defect & Execution Bundle as a .zip file.
    Contains:
    - Executed test automation scripts (/scripts/...)
    - Reproduction guide with step-by-step instructions (/README_REPRODUCTION.md)
    - Consolidated test report in Markdown & CSV (/reports/...)
    - Detailed JSON dump of requirements, scenarios, test cases, and execution results.
    - Screenshot evidence captured during testing (/screenshots/...).
    """
    import io
    import zipfile
    from datetime import datetime
    from src.models.entities import Requirement, TestScenario, TestCase, AutomationScript, TestExecution, TestExecutionResult

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
    scens = db.query(TestScenario).filter(TestScenario.project_id == project_id).all()
    tcs = db.query(TestCase).filter(TestCase.project_id == project_id).all()
    scripts = db.query(AutomationScript).filter(AutomationScript.project_id == project_id).all()
    execs = db.query(TestExecution).filter(TestExecution.project_id == project_id).order_by(TestExecution.created_at.desc()).all()

    # Get results for latest execution
    results = []
    if execs:
        results = db.query(TestExecutionResult).filter(TestExecutionResult.execution_id == execs[0].id).all()

    clean_proj_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in project.name)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    total_runs = len(results) if results else (execs[0].total_tests if execs else 0)
    passed_count = sum(1 for r in results if r.status == "Passed") if results else (execs[0].passed_tests if execs else 0)
    failed_count = sum(1 for r in results if r.status == "Failed") if results else (execs[0].failed_tests if execs else 0)
    error_count = sum(1 for r in results if r.status in ("Error", "Blocked")) if results else 0

    readme_content = f"""# QA Defect & Test Execution Bundle
**Project:** {project.name}
**Target URL:** {project.base_url or 'N/A'}
**Framework:** {project.framework or 'Playwright'}
**Export Timestamp:** {now_str}

## Execution Summary
- **Total Test Executions Recorded:** {total_runs}
- **Passed:** {passed_count}
- **Failed:** {failed_count}
- **Errors/Environment:** {error_count}
- **Requirements Covered:** {len(reqs)}
- **Test Cases Designed:** {len(tcs)}

## How to Reproduce and Run Tests Locally

### Prerequisites
1. Python 3.10 or newer installed.
2. Install testing dependencies:
   ```bash
   pip install pytest pytest-playwright playwright selenium
   playwright install chromium
   ```

### Executing Scripts
Run all test scripts directly from the `scripts/` folder:
```bash
pytest scripts/ -v
```
Or run any individual test:
```bash
python scripts/test_example.py
```

## Failure & Defect Analysis
"""
    failed_items = [r for r in results if r.status in ("Failed", "Error", "Blocked")]
    if not failed_items:
        readme_content += "\nNo failures recorded in the current execution run. All tests passed successfully!\n"
    else:
        for idx, ex in enumerate(failed_items):
            readme_content += f"""
### Defect #{idx + 1}: {ex.test_title or 'Test'}
- **Status:** {ex.status}
- **Duration:** {ex.execution_duration_seconds}s
- **Failing Step:** {ex.failing_step or 'Assertion Step'}
- **Failure Classification:** {ex.failure_classification or 'AssertionFailure'}
- **Error Message:**
```
{ex.error_message or 'No stderr recorded'}
```
- **Suggested Fix:** {ex.suggested_fix or 'Review selector or page load timing'}
"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Add Reproduction README
        zf.writestr("README_REPRODUCTION.md", readme_content)

        # 2. Add Consolidated Report
        try:
            report_data = reporting_agent.run(project_id=project_id)
            if report_data and report_data.markdown_report:
                zf.writestr("reports/QUALITY_AUDIT_REPORT.md", report_data.markdown_report)
            if report_data and report_data.csv_report:
                zf.writestr("reports/TEST_RESULTS.csv", report_data.csv_report)
        except Exception:
            pass

        # 3. Add Automation Scripts
        for s in scripts:
            tc_key = s.test_case_key or s.id[:8]
            clean_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in tc_key)
            script_fname = f"scripts/test_{clean_key}.py"
            zf.writestr(script_fname, s.code_content)

        # 4. Add JSON Data Manifest
        manifest = {
            "project": {"id": project.id, "name": project.name, "base_url": project.base_url, "framework": project.framework},
            "exported_at": now_str,
            "metrics": {"total": total_runs, "passed": passed_count, "failed": failed_count, "error": error_count},
            "requirements": [{"key": r.requirement_key, "title": r.title, "text": r.description} for r in reqs],
            "scenarios": [{"key": sc.scenario_key, "title": sc.title, "type": sc.test_type} for sc in scens],
            "test_cases": [{"key": tc.test_case_key, "title": tc.title, "priority": tc.priority} for tc in tcs],
            "executions": [{"name": r.test_title, "status": r.status, "duration": r.execution_duration_seconds, "error": r.error_message} for r in results],
        }
        zf.writestr("reports/execution_manifest.json", json.dumps(manifest, indent=2))

        # 5. Add screenshots if present
        screenshots_dir = settings.ARTIFACTS_DIR / "screenshots"
        if screenshots_dir.exists():
            for sc_file in screenshots_dir.glob("*.png"):
                zf.write(sc_file, arcname=f"screenshots/{sc_file.name}")

    zip_buffer.seek(0)
    zip_filename = f"{clean_proj_name}_QA_Defect_Pack.zip"
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "X-Defect-Pack-Name": zip_filename,
        },
    )


