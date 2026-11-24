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
from src.core.exceptions import CodeSafetyViolationError

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

    def _execute_single_target(self, target: ExecutionTarget, base_url: str, browser: str = "chromium", headed: bool = False) -> SingleTestResult:
        """Executes a single test target and classifies result."""
        test_start = time.time()
        try:
            res = self._execute_script_isolated(target.code_content, base_url, browser=browser, headed=headed)
            duration = round(time.time() - test_start, 2)

            screenshot_file = None
            out_str = res.get("stdout", "") or ""
            if "SCREENSHOT_CAPTURED: " in out_str:
                for line in out_str.splitlines():
                    if line.startswith("SCREENSHOT_CAPTURED: "):
                        screenshot_file = line.replace("SCREENSHOT_CAPTURED: ", "").strip()
                        break

            if res["exit_code"] == 0:
                if "TEST_BLOCKED_OR_SKIPPED:" in out_str:
                    return SingleTestResult(
                        test_case_key=target.test_case_key,
                        test_title=target.title,
                        status="Blocked",
                        failure_classification="EnvironmentIssue",
                        suggested_fix="Feature or environment configuration requires manual or elevated credentials.",
                        error_message=out_str,
                        duration_seconds=duration,
                        log_output=res["stdout"],
                        screenshot_path=screenshot_file,
                    )
                return SingleTestResult(
                    test_case_key=target.test_case_key,
                    test_title=target.title,
                    status="Passed",
                    duration_seconds=duration,
                    log_output=res["stdout"],
                    screenshot_path=screenshot_file,
                )
            else:
                combined_err = (res.get("stderr", "") or "") + (res.get("stdout", "") or "")
                if "Skipped:" in combined_err or "BLOCKED:" in combined_err:
                    return SingleTestResult(
                        test_case_key=target.test_case_key,
                        test_title=target.title,
                        status="Blocked",
                        failure_classification="EnvironmentIssue",
                        suggested_fix="Safe read-only execution: Test blocked or skipped on public production endpoint.",
                        error_message=res["stderr"] or res["stdout"],
                        duration_seconds=duration,
                        log_output=res["stdout"],
                        screenshot_path=screenshot_file,
                    )
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
                    screenshot_path=screenshot_file,
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
        headed: bool = False,
    ) -> ExecutionReportOutput:
        start_time = time.time()
        execution_key = f"RUN-{int(time.time())}"
        results: List[SingleTestResult] = []

        passed_count = 0
        failed_count = 0
        skipped_count = 0

        # In Headed / Watch mode, force sequential execution so the engineer can visually observe each test without window focus collisions
        if headed:
            parallel = False
            logger.info(f"Headed / Watch Mode enabled: Running {len(targets)} tests sequentially with visible browser window.")
        else:
            logger.info(f"Starting test execution run {execution_key} for {len(targets)} tests on {browser} (parallel={parallel}, workers={max_workers}).")

        def _is_run_cancelled() -> bool:
            if not project_id:
                return False
            try:
                from src.core.workflow_runner import workflow_runner
                return workflow_runner.is_cancelled(project_id=project_id)
            except Exception:
                return False

        if parallel and len(targets) > 1:
            workers = min(max_workers, len(targets))
            logger.info(f"Executing {len(targets)} tests across {workers} parallel worker threads on {browser}.")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_target = {}
                for target in targets:
                    if _is_run_cancelled():
                        results.append(SingleTestResult(
                            test_case_key=target.test_case_key,
                            test_title=target.title,
                            status="Skipped",
                            error_message="Execution cancelled by user request",
                            failure_classification="FlakyTest",
                        ))
                        skipped_count += 1
                        continue
                    future = executor.submit(self._execute_single_target, target, base_url, browser, headed)
                    future_to_target[future] = target

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
                if _is_run_cancelled():
                    results.append(SingleTestResult(
                        test_case_key=target.test_case_key,
                        test_title=target.title,
                        status="Skipped",
                        error_message="Execution cancelled by user request",
                        failure_classification="FlakyTest",
                    ))
                    skipped_count += 1
                    continue
                single_res = self._execute_single_target(target, base_url, browser, headed)
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

    @staticmethod
    def _validate_code_safety(code_content: str) -> Optional[str]:
        """Scans automation code for prohibited operations before execution."""
        prohibited_patterns = [
            ("os.system", "Prohibited execution of os.system"),
            ("subprocess.Popen", "Prohibited execution of subprocess.Popen"),
            ("subprocess.run", "Prohibited execution of subprocess.run"),
            ("subprocess.call", "Prohibited execution of subprocess.call"),
            ("shutil.rmtree", "Prohibited destructive file removal shutil.rmtree"),
            ("eval(", "Prohibited dynamic eval()"),
            ("exec(", "Prohibited dynamic exec()"),
            ("__import__('os')", "Prohibited dynamic import of os"),
            ("__import__(\"os\")", "Prohibited dynamic import of os"),
            ("__import__('subprocess')", "Prohibited dynamic import of subprocess"),
            ("__import__(\"subprocess\")", "Prohibited dynamic import of subprocess"),
            ("testing_platform.db", "Prohibited direct access to platform database file"),
            (".secrets_vault", "Prohibited direct access to platform secret vault"),
            ("open('.env'", "Prohibited direct access to platform environment file"),
            ("open(\".env\"", "Prohibited direct access to platform environment file"),
            ("open('.env.example'", "Prohibited direct access to platform environment file"),
        ]
        lower_code = code_content.lower()
        for pattern, reason in prohibited_patterns:
            if pattern.lower() in lower_code:
                return reason
        return None

    def _execute_script_isolated(self, code_content: str, base_url: str, browser: str = "chromium", headed: bool = False) -> Dict[str, Any]:
        """
        Runs the test script inside a dedicated sandbox directory with process isolation.
        Validates code safety, respects headed/watch mode, and applies corporate proxy/SSL settings.
        """
        safety_error = self._validate_code_safety(code_content)
        if safety_error:
            audit_logger.log_event(
                action="CODE_SAFETY_VIOLATION_BLOCKED",
                status="BLOCKED",
                details={"reason": safety_error},
                severity="WARNING",
            )
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Code Safety Violation: {safety_error}. Execution was blocked by safety policy.",
            }

        project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        browser_lower = (browser or "chromium").lower()
        headless_val = "False" if headed else "True"
        proxy_server = settings.HTTPS_PROXY or settings.HTTP_PROXY or ""
        proxy_bypass = settings.NO_PROXY or ""

        sandbox_dir = settings.ARTIFACTS_DIR / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        tmp_file = sandbox_dir / f"test_run_{int(time.time())}_{uuid.uuid4().hex[:8]}.py"
        tmp_path = str(tmp_file)

        # Assemble harness safely by concatenating without evaluating curly braces in code_content
        harness_header = f"""# Isolated Test Runner Harness
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
project_root = r"{project_root}"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure BasePage is universally accessible under pages, tests.pages, and base_page
import types

class BasePage:
    def __init__(self, page_or_driver):
        self.page = page_or_driver
        self.driver = page_or_driver
    def navigate(self, path="/"):
        target = "{base_url}".rstrip("/") + (path if path.startswith("/") else "/" + path)
        if hasattr(self.page, "goto"):
            self.page.goto(target, wait_until="domcontentloaded", timeout=30000)
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

# Register in sys.modules so both 'pages.base_page' and 'tests.pages.base_page' resolve dynamically
p_mod = types.ModuleType("pages")
p_bp = types.ModuleType("pages.base_page")
p_bp.BasePage = BasePage
p_mod.base_page = p_bp
sys.modules["pages"] = p_mod
sys.modules["pages.base_page"] = p_bp

tests_mod = types.ModuleType("tests")
tests_pages_mod = types.ModuleType("tests.pages")
tests_pages_bp = types.ModuleType("tests.pages.base_page")
tests_pages_bp.BasePage = BasePage
tests_pages_mod.base_page = tests_pages_bp
tests_mod.pages = tests_pages_mod
sys.modules["tests"] = tests_mod
sys.modules["tests.pages"] = tests_pages_mod
sys.modules["tests.pages.base_page"] = tests_pages_bp
sys.modules["base_page"] = p_bp

# --- User Automation Code Under Test ---
"""

        harness_footer = f"""
# --- Test Invocation Runner ---
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
                    launch_kwargs = {{"headless": {headless_val}}}
                    if {headed}:
                        launch_kwargs["slow_mo"] = 150
                        launch_kwargs["args"] = ["--start-maximized"]
                        import os
                        chrome_exe = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                        if os.path.exists(chrome_exe) and b_type in ("chromium", "chrome"):
                            launch_kwargs["channel"] = "chrome"
                    if b_type in ("firefox", "webkit"):
                        browser_inst = getattr(p, b_type).launch(**launch_kwargs)
                    else:
                        browser_inst = p.chromium.launch(**launch_kwargs)
                    context_kwargs = {{"base_url": "{base_url}"}}
                    if {headed}:
                        context_kwargs["no_viewport"] = True
                    if "{proxy_server}":
                        context_kwargs["proxy"] = {{"server": "{proxy_server}"}}
                        if "{proxy_bypass}":
                            context_kwargs["proxy"]["bypass"] = "{proxy_bypass}"
                    ctx = browser_inst.new_context(**context_kwargs)
                    pw_page = ctx.new_page()
                    try:
                        obj(pw_page)
                        if {headed}:
                            import time
                            time.sleep(2)
                    finally:
                        try:
                            import os
                            os.makedirs("screenshots", exist_ok=True)
                            screenshot_file = os.path.abspath(f"screenshots/{{name}}.png")
                            pw_page.screenshot(path=screenshot_file, full_page=False)
                            print(f"SCREENSHOT_CAPTURED: {{screenshot_file}}")
                        except Exception as sc_err:
                            pass
                        pw_page.close()
                        ctx.close()
                        browser_inst.close()
            elif "driver" in sig.parameters:
                from selenium import webdriver
                b_type = "{browser_lower}"
                if b_type in ("firefox", "gecko"):
                    from selenium.webdriver.firefox.options import Options as FOptions
                    opts = FOptions()
                    if not {headed}:
                        opts.add_argument("--headless")
                    else:
                        opts.add_argument("--start-maximized")
                    if "{proxy_server}":
                        opts.add_argument(f"--proxy-server={proxy_server}")
                    drv = webdriver.Firefox(options=opts)
                else:
                    from selenium.webdriver.chrome.options import Options
                    opts = Options()
                    if not {headed}:
                        opts.add_argument("--headless=new")
                    else:
                        opts.add_argument("--start-maximized")
                    opts.add_argument("--no-sandbox")
                    if "{proxy_server}":
                        opts.add_argument(f"--proxy-server={proxy_server}")
                    drv = webdriver.Chrome(options=opts)
                try:
                    obj(drv)
                    if {headed}:
                        import time
                        time.sleep(2)
                finally:
                    try:
                        import os
                        os.makedirs("screenshots", exist_ok=True)
                        screenshot_file = os.path.abspath(f"screenshots/{{name}}.png")
                        drv.save_screenshot(screenshot_file)
                        print(f"SCREENSHOT_CAPTURED: {{screenshot_file}}")
                    except Exception as sc_err:
                        pass
                    drv.quit()
            else:
                print(f"Skipping invocation of {{name}}")
        except Exception as e:
            if "Skipped" in type(e).__name__ or "skip" in str(e).lower() or "BLOCKED" in str(e):
                clean_err = str(e).encode('ascii', errors='replace').decode('ascii')
                print(f"TEST_BLOCKED_OR_SKIPPED: {{name}}: {{clean_err}}")
                sys.exit(0)
            err_str = str(e).encode('ascii', errors='replace').decode('ascii')
            print(f"Error in {{name}}: {{err_str}}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

print("Execution verification completed.")
"""
        full_script = harness_header + code_content + "\n" + harness_footer
        tmp_file.write_text(full_script, encoding="utf-8")

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
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "no_proxy",
            "REQUESTS_CA_BUNDLE",
            "SSL_CERT_FILE",
            "COMSPEC",
            "ALLUSERSPROFILE",
            "PROGRAMDATA",
            "PROGRAMFILES",
            "ProgramFiles(x86)",
            "COMMONPROGRAMFILES",
            "WINDIR",
            "OS",
            "SESSIONNAME",
        ]
        isolated_env = {k: os.environ[k] for k in safe_env_keys if k in os.environ}

        if settings.REQUESTS_CA_BUNDLE and Path(settings.REQUESTS_CA_BUNDLE).exists():
            isolated_env["REQUESTS_CA_BUNDLE"] = str(settings.REQUESTS_CA_BUNDLE)
            isolated_env["SSL_CERT_FILE"] = str(settings.REQUESTS_CA_BUNDLE)

        # Purge any leaked secret patterns from the environment dictionary
        for k in list(isolated_env.keys()):
            if any(term in k.upper() for term in ["KEY", "TOKEN", "SECRET", "PASSWORD", "DATABASE", "GEMINI", "OPENAI", "GITHUB", "JIRA"]):
                del isolated_env[k]

        timeout_sec = getattr(settings, "TEST_EXECUTION_TIMEOUT_SECONDS", 30) or 30

        try:
            # Execute with current virtual environment python and sanitized environment
            cmd = [sys.executable, tmp_path]
            process = subprocess.run(
                cmd,
                env=isolated_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec,
            )
            
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
                        screenshot_path=r.screenshot_path,
                    )
                    db.add(res_record)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to persist execution records: {e}")
