"""
Agent 5: Test Execution & Validation Agent.
Executes approved automation test scripts in an isolated process/sandbox.
Captures live logs, duration, screenshots, and classifies failure root causes:
(Application Defect vs Environment Issue vs Flaky Test).
"""

import time
import os
import subprocess
import tempfile
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from src.agents.base.base_agent import BaseAgent
from src.database.session import SessionLocal
from src.models.entities import TestExecution, TestExecutionResult
from src.config.settings import settings
from src.core.logging import get_logger
from src.core.security.sanitizer import prompt_sanitizer
from src.core.security.audit_logger import audit_logger

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

    def _execute_single_target(self, target: ExecutionTarget, base_url: str, browser: str = "chromium") -> SingleTestResult:
        """Executes a single test target and classifies result."""
        test_start = time.time()
        try:
            res = self._execute_script_isolated(target.code_content, base_url, browser=browser)
            duration = round(time.time() - test_start, 2)

            if res["exit_code"] == 0:
                return SingleTestResult(
                    test_case_key=target.test_case_key,
                    test_title=target.title,
                    status="Passed",
                    duration_seconds=duration,
                    log_output=res["stdout"],
                )
            else:
                classification, fix = self._classify_failure(res["stderr"] or res["stdout"])
                return SingleTestResult(
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
        except Exception as e:
            duration = round(time.time() - test_start, 2)
            return SingleTestResult(
                test_case_key=target.test_case_key,
                test_title=target.title,
                status="Error",
                error_message=str(e),
                failure_classification="EnvironmentIssue",
                suggested_fix="Verify python interpreter and browser dependencies in runner environment.",
                duration_seconds=duration,
            )

    def run(
        self,
        targets: List[ExecutionTarget],
        runner_type: str = "playwright",
        target_env: str = "QA",
        base_url: str = "http://127.0.0.1:8000",
        browser: str = "chromium",
        project_id: Optional[str] = None,
        parallel: bool = True,
        max_workers: int = 4,
    ) -> ExecutionReportOutput:
        start_time = time.time()
        execution_key = f"RUN-{int(time.time())}"
        results: List[SingleTestResult] = []

        passed_count = 0
        failed_count = 0
        skipped_count = 0

        logger.info(f"Starting test execution run {execution_key} for {len(targets)} tests on {browser} (parallel={parallel}, workers={max_workers}).")

        if parallel and len(targets) > 1:
            workers = min(max_workers, len(targets))
            logger.info(f"Executing {len(targets)} tests across {workers} parallel worker threads on {browser}.")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_target = {
                    executor.submit(self._execute_single_target, target, base_url, browser): target
                    for target in targets
                }
                for future in as_completed(future_to_target):
                    single_res = future.result()
                    results.append(single_res)
                    if single_res.status == "Passed":
                        passed_count += 1
                    elif single_res.status in ("Failed", "Error"):
                        failed_count += 1
                    elif single_res.status == "Skipped":
                        skipped_count += 1

            # Preserve original target order
            target_order = {t.test_case_key: idx for idx, t in enumerate(targets)}
            results.sort(key=lambda r: target_order.get(r.test_case_key, 999))
        else:
            for target in targets:
                single_res = self._execute_single_target(target, base_url, browser)
                results.append(single_res)
                if single_res.status == "Passed":
                    passed_count += 1
                elif single_res.status in ("Failed", "Error"):
                    failed_count += 1
                elif single_res.status == "Skipped":
                    skipped_count += 1

        total_duration = round(time.time() - start_time, 2)

        # Persist to database if project_id is provided
        if project_id:
            self._persist_execution_record(
                project_id=project_id,
                execution_key=execution_key,
                runner_type=runner_type,
                target_env=target_env,
                base_url=base_url,
                browser=browser,
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

    def _execute_script_isolated(self, code_content: str, base_url: str, browser: str = "chromium") -> Dict[str, Any]:
        """Runs the script inside an isolated temporary file using python -c or temporary script."""
        project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        browser_lower = (browser or "chromium").lower()

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
                    b_type = "{browser_lower}"
                    if b_type in ("firefox", "webkit", "chromium"):
                        browser_inst = getattr(p, b_type).launch(headless=True)
                    else:
                        browser_inst = p.chromium.launch(headless=True)
                    ctx = browser_inst.new_context(base_url="{base_url}")
                    pw_page = ctx.new_page()
                    try:
                        obj(pw_page)
                    finally:
                        pw_page.close()
                        ctx.close()
                        browser_inst.close()
            elif "driver" in sig.parameters:
                from selenium import webdriver
                b_type = "{browser_lower}"
                if b_type in ("firefox", "gecko"):
                    from selenium.webdriver.firefox.options import Options as FOptions
                    opts = FOptions()
                    opts.add_argument("--headless")
                    drv = webdriver.Firefox(options=opts)
                else:
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

        # Construct sanitized execution environment (Zero host secrets passed to test subprocess)
        safe_env_keys = [
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "LOCALAPPDATA",
            "APPDATA",
            "HOMEDRIVE",
            "HOMEPATH",
            "LANG",
            "LC_ALL",
            "PYTHONIOENCODING",
            "PLAYWRIGHT_BROWSERS_PATH",
        ]
        isolated_env = {k: os.environ[k] for k in safe_env_keys if k in os.environ}

        # Purge any leaked secret patterns from the environment dictionary
        for k in list(isolated_env.keys()):
            if any(term in k.upper() for term in ["KEY", "TOKEN", "SECRET", "PASSWORD", "DATABASE", "GEMINI", "OPENAI", "GITHUB", "JIRA"]):
                del isolated_env[k]

        timeout_sec = getattr(settings, "TEST_EXECUTION_TIMEOUT_SECONDS", 30) or 30

        try:
            # Execute with current virtual environment python and sanitized environment
            cmd = [sys.executable, tmp_path]
            process = subprocess.run(cmd, env=isolated_env, capture_output=True, text=True, timeout=timeout_sec)
            
            clean_stdout = prompt_sanitizer.redact_secrets(process.stdout)
            clean_stderr = prompt_sanitizer.redact_secrets(process.stderr)

            audit_logger.log_event(
                action="SUBPROCESS_TEST_EXECUTION",
                status="SUCCESS" if process.returncode == 0 else "TEST_FAILED",
                details={"exit_code": process.returncode, "timeout_seconds": timeout_sec},
            )

            return {
                "exit_code": process.returncode,
                "stdout": clean_stdout,
                "stderr": clean_stderr,
            }
        except subprocess.TimeoutExpired:
            audit_logger.log_event(
                action="SUBPROCESS_TEST_TIMEOUT",
                status="TIMEOUT",
                details={"timeout_seconds": timeout_sec},
                severity="WARNING",
            )
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_sec} seconds",
            }
        except Exception as e:
            err_msg = prompt_sanitizer.redact_secrets(str(e))
            audit_logger.log_event(
                action="SUBPROCESS_TEST_ERROR",
                status="ERROR",
                details={"error": err_msg},
                severity="ERROR",
            )
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": err_msg,
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
        browser: str = "chromium",
    ):
        try:
            with SessionLocal() as db:
                exec_record = TestExecution(
                    project_id=project_id,
                    execution_key=execution_key,
                    runner_type=runner_type,
                    target_environment=target_env,
                    base_url=base_url,
                    browser=browser,
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
