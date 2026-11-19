"""
System-wide Dashboard Overview API Endpoints.
Aggregates real-time metrics across all projects, test cases, executions, and AI models.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
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
    CustomAgent,
    AuditLog,
)
from src.llm.registry.model_registry import model_registry
from src.llm.router.agent_model_router import agent_model_router

router = APIRouter(prefix="/dashboard", tags=["Dashboard Overview"])


@router.get("/overview", response_model=Dict[str, Any])
def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Returns full system metrics matching the reference dashboard UI:
    - 4 KPI cards: Total Projects, AI Agents, Test Cases, Executions
    - My Projects list with real metadata
    - AI Model Status (Gemini & OpenAI connectivity + active models)
    - Testing Overview: 7-day spline trend, success rate donut gauge, passed/failed/blocked breakdown
    - Recent Activity stream
    """
    # 1. KPI Counts
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    total_projects = len(projects)

    custom_agents_count = db.query(CustomAgent).filter(CustomAgent.is_active == True).count()
    total_agents = 6 + custom_agents_count

    total_test_cases = db.query(TestCase).count()
    executions = db.query(TestExecution).order_by(TestExecution.created_at.desc()).all()
    total_executions = len(executions)

    total_passed = sum(e.passed_tests for e in executions)
    total_failed = sum(e.failed_tests for e in executions)
    total_blocked = sum(e.blocked_tests for e in executions)
    total_skipped = sum(e.skipped_tests for e in executions)
    total_evaluated = total_passed + total_failed + total_blocked + total_skipped

    success_rate = round((total_passed / total_evaluated * 100), 1) if total_evaluated > 0 else 0.0

    # 2. AI Model Status
    provider_status = model_registry.test_providers()
    agent_configs = agent_model_router.get_all_configurations()
    default_gemini = agent_configs.get("agent_1_requirement_analysis", {}).get("model_id", "gemini-2.5-flash")
    default_openai = "gpt-5.1" if provider_status.get("openai") else "Not configured"

    ai_model_status = {
        "gemini": {
            "name": "Gemini",
            "connected": provider_status.get("gemini", False),
            "selected_model": default_gemini,
        },
        "openai": {
            "name": "OpenAI",
            "connected": provider_status.get("openai", False),
            "selected_model": default_openai,
        },
        "all_connected": provider_status.get("gemini", False) or provider_status.get("openai", False),
    }

    # 3. Recent Projects Listing
    recent_projects_data = []
    for p in projects[:6]:
        p_cases = db.query(TestCase).filter(TestCase.project_id == p.id).count()
        p_execs = db.query(TestExecution).filter(TestExecution.project_id == p.id).count()
        recent_projects_data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description or "Automated software testing project",
            "framework": p.framework,
            "base_url": p.base_url,
            "status": "Active" if p_execs > 0 or p_cases > 0 else "Idle",
            "agent_count": 6,
            "test_cases_count": p_cases,
            "executions_count": p_execs,
            "last_updated": p.updated_at.isoformat() if p.updated_at else p.created_at.isoformat(),
        })

    # 4. 7-Day Trend Chart Data (Mon - Sun)
    days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    now = datetime.utcnow()
    # Map each weekday to execution counts
    day_counts = {i: 0 for i in range(7)}
    for e in executions:
        if e.created_at and (now - e.created_at).days < 7:
            weekday = e.created_at.weekday()
            day_counts[weekday] += (e.passed_tests + e.failed_tests + e.blocked_tests) or 1

    chart_trend_data = [day_counts[i] for i in range(7)]
    if sum(chart_trend_data) == 0:
        # Default baseline if zero runs yet in past week
        chart_trend_data = [0, 0, 0, 0, 0, 0, total_evaluated if total_evaluated > 0 else 0]

    # 5. Recent Activity List
    recent_activities: List[Dict[str, Any]] = []
    # Test executions activity
    for ex in executions[:4]:
        p_name = next((p.name for p in projects if p.id == ex.project_id), "Client Project")
        recent_activities.append({
            "id": ex.id,
            "type": "execution",
            "status": "success" if ex.failed_tests == 0 else "failure",
            "title": f"Test execution completed ({ex.passed_tests} passed, {ex.failed_tests} failed)",
            "project_name": p_name,
            "project_id": ex.project_id,
            "timestamp": ex.created_at.isoformat() if ex.created_at else now.isoformat(),
        })

    # Recent test cases activity
    recent_cases = db.query(TestCase).order_by(TestCase.created_at.desc()).limit(3).all()
    for tc in recent_cases:
        p_name = next((p.name for p in projects if p.id == tc.project_id), "Project")
        recent_activities.append({
            "id": tc.id,
            "type": "test_case",
            "status": "info",
            "title": f"Test case created: {tc.test_case_key} - {tc.title}",
            "project_name": p_name,
            "project_id": tc.project_id,
            "timestamp": tc.created_at.isoformat() if tc.created_at else now.isoformat(),
        })

    # Sort activities by timestamp descending
    recent_activities.sort(key=lambda a: a["timestamp"], reverse=True)

    return {
        "kpis": {
            "total_projects": total_projects,
            "total_agents": total_agents,
            "total_test_cases": total_test_cases,
            "total_executions": total_executions,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "blocked_tests": total_blocked,
            "skipped_tests": total_skipped,
            "success_rate": success_rate,
        },
        "ai_model_status": ai_model_status,
        "recent_projects": recent_projects_data,
        "testing_overview": {
            "days": days_labels,
            "trend": chart_trend_data,
            "success_rate": success_rate,
            "passed": total_passed,
            "failed": total_failed,
            "blocked": total_blocked,
        },
        "recent_activity": recent_activities[:6],
    }
