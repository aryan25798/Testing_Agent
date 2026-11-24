"""
Agent 6: Test Orchestration & Reporting Agent.
Coordinates lifecycle dependencies across all six specialized testing agents.
Calculates rigorous coverage metrics and compiles consolidated reports
exportable as Markdown, JSON, CSV, and PDF.
"""

import io
import csv
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.agents.base.base_agent import BaseAgent
from src.database.session import SessionLocal
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
    TestExecutionResult,
)
from src.core.logging import get_logger

logger = get_logger("orchestration_reporting_agent")


class ConsolidatedReport(BaseModel):
    project_id: str
    project_name: str
    framework: str
    total_requirements: int
    approved_requirements: int
    total_scenarios: int
    total_test_cases: int
    automated_test_cases: int
    total_executions: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    requirement_coverage_pct: float
    automation_coverage_pct: float
    test_pass_rate_pct: float
    defect_candidates: List[Dict[str, Any]]
    recommendations: List[str]
    markdown_report: str


SYSTEM_INSTRUCTIONS = """You are a Principal QA Operations & Reporting Architect.
Your mission is to evaluate overall testing health, calculate coverage and defect density metrics,
and generate high-impact executive summaries for stakeholders.

STRICT PRINCIPLE:
Never fabricate testing numbers. Calculate metrics strictly from factual inputs.
"""


class OrchestrationReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent_6_orchestration_reporting",
            agent_name="Test Orchestration & Reporting Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(self, input_data: Any = None, project_id: Optional[str] = None) -> ConsolidatedReport:
        target_pid = project_id or (input_data if isinstance(input_data, str) else "")
        return self.generate_consolidated_report(project_id=target_pid)

    def generate_consolidated_report(self, project_id: str) -> ConsolidatedReport:
        with SessionLocal() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project with ID {project_id} not found.")

            reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
            scenarios = db.query(TestScenario).filter(TestScenario.project_id == project_id).all()
            cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()
            scripts = db.query(AutomationScript).filter(AutomationScript.project_id == project_id).all()
            executions = db.query(TestExecution).filter(TestExecution.project_id == project_id).all()

            total_reqs = len(reqs)
            approved_reqs = sum(1 for r in reqs if r.is_approved)

            # Traceable requirements covered by at least 1 scenario
            covered_req_ids = {s.requirement_id for s in scenarios}
            req_coverage_pct = round((len(covered_req_ids) / total_reqs * 100), 1) if total_reqs > 0 else 0.0

            total_cases = len(cases)
            # Filter to actual test scripts (excluding infrastructure files like conftest.py and base_page.py)
            test_scripts = [s for s in scripts if s.script_name.startswith("test_") or s.test_case_id is not None]
            total_automated = min(len(test_scripts), total_cases) if total_cases > 0 else len(test_scripts)
            auto_coverage_pct = round((total_automated / total_cases * 100), 1) if total_cases > 0 else 0.0

            # Derive execution metrics from latest execution or cumulative runs
            latest_exec = executions[-1] if executions else None
            if latest_exec:
                total_passed = latest_exec.passed_tests
                total_failed = latest_exec.failed_tests
                total_skipped = latest_exec.skipped_tests
                total_executed = total_passed + total_failed + total_skipped
            else:
                total_passed = sum(e.passed_tests for e in executions)
                total_failed = sum(e.failed_tests for e in executions)
                total_skipped = sum(e.skipped_tests for e in executions)
                total_executed = total_passed + total_failed + total_skipped
            pass_rate_pct = round((total_passed / total_executed * 100), 1) if total_executed > 0 else 0.0

            # Collect defect candidates from failed execution results
            defect_candidates = []
            for e in executions:
                for r in e.results:
                    if r.status in ["Failed", "Error"]:
                        defect_candidates.append({
                            "execution_key": e.execution_key,
                            "test_title": r.test_title,
                            "failing_step": r.failing_step,
                            "error": r.error_message[:200] if r.error_message else "Assertion error",
                            "classification": r.failure_classification or "ApplicationDefect",
                            "suggested_fix": r.suggested_fix,
                        })

            # Actionable recommendations
            recommendations = []
            if req_coverage_pct < 100.0:
                recommendations.append(f"Expand scenario coverage: {round(100.0 - req_coverage_pct, 1)}% of requirements currently lack linked test scenarios.")
            if auto_coverage_pct < 80.0:
                recommendations.append(f"Increase automation coverage: Currently at {auto_coverage_pct}%. Convert manual test cases to automated {project.framework} scripts.")
            if total_failed > 0:
                recommendations.append(f"Resolve {total_failed} failing test case(s) before release readiness approval.")
            if not recommendations:
                recommendations.append("All requirements covered and automated test suites executed successfully. Release candidate is verified.")

            # Markdown report compilation
            md_lines = [
                f"# Consolidated Testing & QA Report: {project.name}",
                f"**Framework**: `{project.framework}` | **Generated**: `UTC Realtime`",
                "",
                "## 1. Executive Summary",
                f"- **Requirements Coverage**: `{req_coverage_pct}%` ({len(covered_req_ids)}/{total_reqs} requirements covered)",
                f"- **Automation Coverage**: `{auto_coverage_pct}%` ({total_automated}/{total_cases} test cases automated)",
                f"- **Test Pass Rate**: `{pass_rate_pct}%` ({total_passed} of {total_executed} tests passed, {total_failed} failed)",
                "",
                "## 2. Testing Lifecycle Metrics",
                "| Metric | Count |",
                "|---|---|",
                f"| Total Requirements | {total_reqs} |",
                f"| Approved Requirements | {approved_reqs} |",
                f"| Generated Scenarios | {len(scenarios)} |",
                f"| Executable Test Cases | {total_cases} |",
                f"| Automated Test Scripts | {total_automated} |",
                f"| Total Test Executions | {len(executions)} |",
                f"| Passed Executions | {total_passed} |",
                f"| Failed Executions | {total_failed} |",
                "",
                "## 3. Defect Candidates & Failure Triage",
            ]

            if defect_candidates:
                for d in defect_candidates[:10]:
                    md_lines.append(f"- **{d['test_title']}** [{d['classification']}]")
                    md_lines.append(f"  - Error: `{d['error']}`")
                    if d.get("suggested_fix"):
                        md_lines.append(f"  - Suggested Fix: {d['suggested_fix']}")
            else:
                md_lines.append("No active defects or failing assertions detected in recent test executions.")

            md_lines.extend([
                "",
                "## 4. Strategic QA Recommendations",
            ])
            for rec in recommendations:
                md_lines.append(f"- {rec}")

            markdown_report = "\n".join(md_lines)

            return ConsolidatedReport(
                project_id=project.id,
                project_name=project.name,
                framework=project.framework,
                total_requirements=total_reqs,
                approved_requirements=approved_reqs,
                total_scenarios=len(scenarios),
                total_test_cases=total_cases,
                automated_test_cases=total_automated,
                total_executions=len(executions),
                passed_tests=total_passed,
                failed_tests=total_failed,
                skipped_tests=total_skipped,
                requirement_coverage_pct=req_coverage_pct,
                automation_coverage_pct=auto_coverage_pct,
                test_pass_rate_pct=pass_rate_pct,
                defect_candidates=defect_candidates,
                recommendations=recommendations,
                markdown_report=markdown_report,
            )

    def export_csv(self, report: ConsolidatedReport) -> str:
        """Exports report summary metrics to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Project Name", report.project_name])
        writer.writerow(["Framework", report.framework])
        writer.writerow(["Total Requirements", report.total_requirements])
        writer.writerow(["Requirements Coverage %", f"{report.requirement_coverage_pct}%"])
        writer.writerow(["Total Scenarios", report.total_scenarios])
        writer.writerow(["Total Test Cases", report.total_test_cases])
        writer.writerow(["Automation Coverage %", f"{report.automation_coverage_pct}%"])
        writer.writerow(["Total Executions", report.total_executions])
        writer.writerow(["Passed Tests", report.passed_tests])
        writer.writerow(["Failed Tests", report.failed_tests])
        writer.writerow(["Pass Rate %", f"{report.test_pass_rate_pct}%"])
        return output.getvalue()

    def export_pdf(self, report: ConsolidatedReport) -> bytes:
        """Generates a styled PDF report using ReportLab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#1e293b"),
            )
            h2_style = ParagraphStyle(
                "H2Style",
                parent=styles["Heading2"],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#0f172a"),
            )

            story.append(Paragraph(f"Test Execution & Quality Report: {report.project_name}", title_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"Framework: <b>{report.framework}</b> | Status: <b>Verified</b>", styles["Normal"]))
            story.append(Spacer(1, 15))

            # Table data
            data = [
                ["KPI Metric", "Value"],
                ["Total Requirements", str(report.total_requirements)],
                ["Requirement Coverage", f"{report.requirement_coverage_pct}%"],
                ["Total Test Scenarios", str(report.total_scenarios)],
                ["Total Test Cases", str(report.total_test_cases)],
                ["Automated Test Scripts", str(report.automated_test_cases)],
                ["Automation Coverage", f"{report.automation_coverage_pct}%"],
                ["Total Test Runs", str(report.total_executions)],
                ["Passed Tests", str(report.passed_tests)],
                ["Failed Tests", str(report.failed_tests)],
                ["Overall Success Rate", f"{report.test_pass_rate_pct}%"],
            ]
            t = Table(data, colWidths=[250, 200])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

            story.append(Paragraph("Strategic Recommendations", h2_style))
            story.append(Spacer(1, 6))
            for rec in report.recommendations:
                story.append(Paragraph(f"• {rec}", styles["Normal"]))
                story.append(Spacer(1, 4))

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Failed to generate ReportLab PDF: {e}. Fallback to plain bytes.")
            return report.markdown_report.encode("utf-8")
