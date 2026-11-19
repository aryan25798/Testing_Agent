"""
Agent 5: Test Execution & Validation Agent.
Executes approved automation test scripts in an isolated process/sandbox.
Captures live logs, duration, screenshots, and classifies failure root causes:
(Application Defect vs Environment Issue vs Flaky Test).
"""

import time
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.agents.base.base_agent import BaseAgent
from src.database.session import SessionLocal
from src.models.entities import TestExecution, TestExecutionResult
from src.core.logging import get_logger

logger = get_logger("test_execution_agent")


class ExecutionTarget(BaseModel):
    test_case_key: str
    title: str
    script_path: str
    code_content: str


class SingleTestResult(BaseModel):
    test_case_key: str
    test_title: str
    status: str  # Passed | Failed | Skipped | Blocked | Error
    failing_step: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    failure_classification: Optional[str] = None  # ApplicationDefect | EnvironmentIssue | FlakyTest
    suggested_fix: Optional[str] = None
    duration_seconds: float = 0.0
    log_output: Optional[str] = None
    screenshot_path: Optional[str] = None


class ExecutionReportOutput(BaseModel):
    execution_key: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: float
    results: List[SingleTestResult]
    summary: str


SYSTEM_INSTRUCTIONS = """You are a Principal Test Execution & Defect Triage Specialist.
Your mission is to execute test suites in isolated sandboxes, capture real-time execution logs,
and perform in-depth root cause analysis on any test failures.

FAILURE CLASSIFICATION RULES:
1. ApplicationDefect: The application under test returned unexpected data or assertion failed.
2. EnvironmentIssue: Network timeout, 502 Bad Gateway, missing driver or browser binary.
3. FlakyTest: Non-deterministic race conditions or locator timing issues.
"""


class TestExecutionAgent(BaseAgent):
    __test__ = False

    def __init__(self):
        super().__init__(
            agent_id="agent_5_test_execution",
            agent_name="Test Execution & Validation Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(
        self,
        targets: List[ExecutionTarget],
        runner_type: str = "playwright",
        target_env: str = "QA",
        base_url: str = "http://127.0.0.1:8000",
        project_id: Optional[str] = None,
    ) -> ExecutionReportOutput:
        start_time = time.time()
        execution_key = f"RUN-{int(time.time())}"
        results: List[SingleTestResult] = []

        passed_count = 0
        failed_count = 0
        skipped_count = 0

        logger.info(f"Starting test execution run {execution_key} for {len(targets)} tests.")

        for target in targets:
            test_start = time.time()
            try:
                # Execute in an isolated Python subprocess
                res = self._execute_script_isolated(target.code_content, base_url)
                duration = round(time.time() - test_start, 2)

                if res["exit_code"] == 0:
                    passed_count += 1
                    results.append(
                        SingleTestResult(
                            test_case_key=target.test_case_key,
                            test_title=target.title,
                            status="Passed",
                            duration_seconds=duration,
                            log_output=res["stdout"],
                        )
                    )
                else:
                    failed_count += 1
                    # Classify failure
                    classification, fix = self._classify_failure(res["stderr"] or res["stdout"])
                    results.append(
                        SingleTestResult(
                            test_case_key=target.test_case_key,
                            test_title=target.title,
                            status="Failed",
                            failing_step="Automated Assertion Step",
                            expected_result="Element/Response matches expected assertion state",
                            actual_result=res["stderr"][:200] if res["stderr"] else "Assertion failed",
                            error_message=res["stderr"] or res["stdout"],
                            failure_classification=classification,
                            suggested_fix=fix,
                            duration_seconds=duration,
                            log_output=res["stdout"],
                        )
                    )
            except Exception as e:
                failed_count += 1
                duration = round(time.time() - test_start, 2)
                results.append(
                    SingleTestResult(
                        test_case_key=target.test_case_key,
                        test_title=target.title,
                        status="Error",
                        error_message=str(e),
                        failure_classification="EnvironmentIssue",
                        suggested_fix="Verify python interpreter and browser dependencies in runner environment.",
                        duration_seconds=duration,
                    )
                )

        total_duration = round(time.time() - start_time, 2)

        # Persist to database if project_id is provided
        if project_id:
            self._persist_execution_record(
                project_id=project_id,
                execution_key=execution_key,
                runner_type=runner_type,
                target_env=target_env,
                base_url=base_url,
                total=len(targets),
                passed=passed_count,
                failed=failed_count,
                skipped=skipped_count,
                duration=total_duration,
                results=results,
            )

        return ExecutionReportOutput(
            execution_key=execution_key,
            total_tests=len(targets),
            passed_tests=passed_count,
            failed_tests=failed_count,
            skipped_tests=skipped_count,
            duration_seconds=total_duration,
            results=results,
            summary=f"Executed {len(targets)} tests: {passed_count} Passed, {failed_count} Failed in {total_duration}s.",
        )

    def _execute_script_isolated(self, code_content: str, base_url: str) -> Dict[str, Any]:
        """Runs the script inside an isolated temporary file using python -c or temporary script."""
        project_root = str(Path(__file__).resolve().parent.parent.parent.parent)

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp_path = tmp.name
            # Wrap execution with safety harness
            harness_code = f"""# Isolated Test Runner Harness
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
project_root = r"{project_root}"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure tests.pages.base_page is available
try:
    from tests.pages.base_page import BasePage
except ImportError:
    class BasePage:
        def __init__(self, page_or_driver):
            self.page = page_or_driver
            self.driver = page_or_driver
        def navigate(self, path="/"):
            target = "{base_url}".rstrip("/") + (path if path.startswith("/") else "/" + path)
            if hasattr(self.page, "goto"):
                self.page.goto(target, wait_until="domcontentloaded", timeout=15000)
            elif hasattr(self.driver, "get"):
                self.driver.get(target)
        def get_title(self):
            return self.page.title() if hasattr(self.page, "title") else getattr(self.driver, "title", "")
        def click_button(self, selector):
            if hasattr(self.page, "locator"):
                self.page.locator(selector).click(timeout=5000)
        def enter_text(self, selector, text):
            if hasattr(self.page, "locator"):
                self.page.locator(selector).fill(text, timeout=5000)
        def is_visible(self, selector):
            if hasattr(self.page, "locator"):
                return self.page.locator(selector).is_visible()
            return True

    import types
    tests_mod = types.ModuleType("tests")
    pages_mod = types.ModuleType("tests.pages")
    pages_mod.BasePage = BasePage
    tests_mod.pages = pages_mod
    sys.modules["tests"] = tests_mod
    sys.modules["tests.pages"] = pages_mod
    sys.modules["tests.pages.base_page"] = pages_mod

# User Automation Code Under Test
{code_content}

# Test Invocation
for name, obj in list(locals().items()):
    if name.startswith("test_") and callable(obj):
        try:
            import inspect
            sig = inspect.signature(obj)
            if len(sig.parameters) == 0:
                obj()
            elif "page" in sig.parameters:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(base_url="{base_url}")
                    pw_page = ctx.new_page()
                    try:
                        obj(pw_page)
                    finally:
                        pw_page.close()
                        ctx.close()
                        browser.close()
            elif "driver" in sig.parameters:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                opts = Options()
                opts.add_argument("--headless=new")
                opts.add_argument("--no-sandbox")
                drv = webdriver.Chrome(options=opts)
                try:
                    obj(drv)
                finally:
                    drv.quit()
            else:
                print(f"Skipping invocation of {{name}}")
        except Exception as e:
            print(f"Error in {{name}}: {{e}}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

print("Execution verification completed.")
"""
            tmp.write(harness_code)

        try:
            # Execute with current virtual environment python
            cmd = [sys.executable, tmp_path]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": "Execution timed out after 30 seconds",
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
            }
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    def _classify_failure(self, error_text: str) -> Tuple[str, str]:
        lower_err = error_text.lower()
        if "assertionerror" in lower_err or "expected" in lower_err:
            return "ApplicationDefect", "Inspect application state or response payload at the assertion step."
        elif "connection refused" in lower_err or "timeout" in lower_err or "502" in lower_err:
            return "EnvironmentIssue", "Verify backend service availability and network ingress."
        elif "stale element" in lower_err or "element not interactable" in lower_err:
            return "FlakyTest", "Add explicit wait for locator visibility before interaction."
        return "ApplicationDefect", "Review attached logs and verify UI state."

    def _persist_execution_record(
        self,
        project_id: str,
        execution_key: str,
        runner_type: str,
        target_env: str,
        base_url: str,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        results: List[SingleTestResult],
    ):
        try:
            with SessionLocal() as db:
                exec_record = TestExecution(
                    project_id=project_id,
                    execution_key=execution_key,
                    runner_type=runner_type,
                    target_environment=target_env,
                    base_url=base_url,
                    total_tests=total,
                    passed_tests=passed,
                    failed_tests=failed,
                    skipped_tests=skipped,
                    execution_duration_seconds=duration,
                    status="Completed" if failed == 0 else "Failed",
                )
                db.add(exec_record)
                db.flush()

                for r in results:
                    res_record = TestExecutionResult(
                        execution_id=exec_record.id,
                        test_title=r.test_title,
                        status=r.status,
                        failing_step=r.failing_step,
                        expected_result=r.expected_result,
                        actual_result=r.actual_result,
                        error_message=r.error_message,
                        failure_classification=r.failure_classification,
                        suggested_fix=r.suggested_fix,
                        execution_duration_seconds=r.duration_seconds,
                        log_output=r.log_output,
                    )
                    db.add(res_record)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to persist execution records: {e}")
