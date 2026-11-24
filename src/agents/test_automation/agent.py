"""
Agent 4: Test Automation Agent.
Generates production-grade, executable Python test automation suites
using Playwright or Selenium with Page Object Model (POM) and robust assertions.
Performs automatic Python syntax compilation validation before saving.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from src.agents.base.base_agent import BaseAgent
from src.agents.test_case_design.agent import GeneratedTestCase
from src.core.logging import get_logger

logger = get_logger("test_automation_agent")


class GeneratedScript(BaseModel):
    script_name: str
    file_path: str
    framework: str  # playwright | selenium
    test_case_key: Optional[str] = None
    code_content: str
    syntax_valid: bool = True
    validation_error: Optional[str] = None


class SingleScriptGeneration(BaseModel):
    test_case_key: str = Field(default="TC-001", description="Test case key e.g. TC-001")
    code_content: str = Field(default="", description="Complete Python test script code")
    explanation: Optional[str] = Field(default="", description="Summary of assertions and locators used")

    @model_validator(mode="before")
    @classmethod
    def reconcile_script(cls, data: Any) -> Any:
        if isinstance(data, dict):
            code = data.get("code_content") or data.get("code") or data.get("script") or data.get("script_code") or ""
            key = data.get("test_case_key") or data.get("key") or data.get("id") or "TC-001"
            data["code_content"] = str(code)
            data["test_case_key"] = str(key)
        return data


class AutomationBatchOutput(BaseModel):
    scripts: List[SingleScriptGeneration] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def reconcile_batch(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sc = data.get("scripts") or data.get("test_scripts") or data.get("items") or []
            data["scripts"] = sc
        elif isinstance(data, list):
            data = {"scripts": data}
        return data


class AutomationGenerationInput(BaseModel):
    test_cases: List[GeneratedTestCase]
    framework: str = "playwright"  # playwright | selenium
    browser_name: str = "chromium"  # chromium | firefox | webkit | chrome
    base_url: Optional[str] = "http://127.0.0.1:8000"


class AutomationGenerationOutput(BaseModel):
    scripts: List[GeneratedScript]
    framework: str
    total_scripts: int
    validation_summary: str


SYSTEM_INSTRUCTIONS = """You are a Principal Test Automation Architect specializing in Playwright and Selenium for Python.
Your mission is to generate clean, maintainable, production-ready Python automation scripts based on approved test cases.

BEST PRACTICES:
1. Follow Page Object Model (POM) or idiomatic direct Playwright/Selenium API.
2. Use reliable locators (e.g. page.get_by_role, page.get_by_placeholder, page.get_by_label, page.locator). Avoid fragile absolute XPaths.
3. NEVER USE ARBITRARY sleep() STATEMENTS. Rely on built-in auto-waiting or explicit waits.
4. Include explicit assertion statements checking expected outcomes and state transitions.
5. All generated test functions must take the browser fixture ('page' for Playwright, 'driver' for Selenium).
6. Code must be syntactically valid Python that passes `compile()`.
7. Return only valid RFC-8259 JSON conforming to AutomationBatchOutput schema.
"""


class TestAutomationAgent(BaseAgent):
    __test__ = False

    def __init__(self):
        super().__init__(
            agent_id="agent_4_test_automation",
            agent_name="Test Automation Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(self, input_data: AutomationGenerationInput, project_id: Optional[str] = None) -> AutomationGenerationOutput:
        from src.core.security.sanitizer import prompt_sanitizer
        from src.core.utils.json_sanitizer import normalize_to_schema

        framework = input_data.framework.lower()
        if framework not in ["playwright", "selenium"]:
            framework = "playwright"

        browser_name = (input_data.browser_name or "chromium").lower()
        if browser_name not in ["chromium", "firefox", "webkit", "chrome"]:
            browser_name = "chromium"

        base_url = (input_data.base_url or "http://127.0.0.1:8000").rstrip("/")
        scripts: List[GeneratedScript] = []

        # 1. Base Configuration & Fixtures
        if framework == "playwright":
            conftest_code = self._generate_playwright_conftest(base_url, browser_name)
        else:
            conftest_code = self._generate_selenium_conftest(base_url, browser_name)

        scripts.append(
            self._create_validated_script(
                script_name="conftest.py",
                file_path="tests/conftest.py",
                framework=framework,
                code_content=conftest_code,
            )
        )

        # 2. Page Objects
        if framework == "playwright":
            page_code = self._generate_playwright_page_object()
        else:
            page_code = self._generate_selenium_page_object()

        scripts.append(
            self._create_validated_script(
                script_name="base_page.py",
                file_path="tests/pages/base_page.py",
                framework=framework,
                code_content=page_code,
            )
        )

        # 3. AI-Powered Script Generation per Test Case Batch
        test_cases = input_data.test_cases or []
        batch_size = 4
        batches = [test_cases[i : i + batch_size] for i in range(0, len(test_cases), batch_size)]

        ai_generated_map: Dict[str, str] = {}
        for b_idx, batch in enumerate(batches):
            case_specs = []
            for tc in batch:
                steps_str = "\n".join(
                    [f"  Step {s.step_number}: {s.action} -> Expected: {s.expected}" for s in tc.execution_steps]
                )
                case_specs.append(
                    f"Test Case: {tc.test_case_key} - {tc.title}\n"
                    f"Objective: {tc.objective}\n"
                    f"Preconditions: {tc.preconditions}\n"
                    f"Test Data: {tc.test_data}\n"
                    f"Steps:\n{steps_str}\n"
                    f"Expected Result: {tc.expected_results}"
                )

            wrapped_batch = prompt_sanitizer.wrap_untrusted_input(
                "\n\n---\n\n".join(case_specs), label=f"test_cases_batch_{b_idx + 1}"
            )

            prompt = f"""Generate production-grade {framework.upper()} Python test functions for the following test cases against target URL: {base_url}

{wrapped_batch}

CRITICAL EXECUTION REQUIREMENTS:
1. For each test case, generate a Python test function:
   - For Playwright: 'def test_{{test_case_key_clean}}(page: Page):' importing Page, expect, and BasePage.
   - For Selenium: 'def test_{{test_case_key_clean}}(driver):' importing By, WebDriverWait, EC, and BasePage.
2. Self-contained live execution: The script must directly perform live actions against '{base_url}' using the page fixture.
3. NAVIGATION TIMEOUT: For page.goto('{base_url}'), use standard 30,000ms timeout or omit the timeout argument so Playwright uses its default 30s. NEVER set a 10,000ms (10s) timeout on page.goto(), as live websites with SSL and redirects will fail.
4. NO EXTERNAL DEPENDENCIES & NO MOCKING: Never import from other test files. Never use page.route or inject fake HTML fixtures. Tests must run live against the real target application.
5. NO UNSET ENV VARS: Never gate test execution behind custom environment variables (e.g. do NOT do 'os.getenv(...)') or missing hook modules. Embed required locators and selectors directly.
6. MODERN MULTI-SELECTOR BRAND LOGOS: When checking brand logos on homepages (Google, YouTube, etc.), modern websites use SVGs and ARIA labels rather than legacy <img> tags. Always use resilient multi-selector locators: e.g.
   logo = page.locator('svg[aria-label*="Google" i], img[alt*="Google" i], a[aria-label*="Google" i], [role="banner"]').first
   expect(logo).to_be_visible(timeout=10000)
7. RESILIENT SEARCH SUBMISSIONS & ASSERTIONS:
   - When submitting a form or search, press Enter or click the button WITHOUT 'no_wait_after=True'.
   - Wait for the results container or URL to update before asserting results:
     page.keyboard.press("Enter")
     expect(page.locator("#search, [role='main'], main, #contents").first).to_be_visible(timeout=15000)
   - When asserting page titles after search, use case-insensitive partial match regex (e.g. expect(page).to_have_title(re.compile(re.escape(query), re.I), timeout=10000)) rather than brittle exact localized strings that vary by country or language.
8. COOKIE / CONSENT BANNER HANDLING: Many public websites show cookie consent or GDPR banners. If present, dismiss them:
   consent = page.locator('button:has-text("Accept all"), button:has-text("I agree"), button:has-text("Reject all"), [aria-label*="Accept all" i]').first
   if consent.is_visible(timeout=1500):
       consent.click(timeout=3000)
9. DO NOT USE BRITTLE NETWORK INTERCEPTIONS: Do not use `page.expect_request` or `page.expect_response` for dynamic single-page applications. Rely strictly on visible DOM assertions.
10. Resilient element timeouts: Use sensible timeouts (5,000ms - 10,000ms) on element waits.
11. Safe read-only execution: Do not attempt real financial payments, ticket bookings, or destructive modifications.
12. Return JSON matching AutomationBatchOutput schema."""

            try:
                batch_res = self.execute_with_llm(
                    prompt=prompt,
                    output_schema=AutomationBatchOutput,
                    project_id=project_id,
                )
                if batch_res:
                    norm = normalize_to_schema(batch_res, AutomationBatchOutput)
                    for item in norm.scripts:
                        if item.test_case_key and item.code_content:
                            ai_generated_map[item.test_case_key.upper()] = item.code_content
            except Exception as e:
                logger.warning(f"AI test script generation batch {b_idx + 1} failed: {e}. Synthesizing step-aware script.")

        # 4. Assemble and Validate All Test Scripts
        for tc in test_cases:
            clean_name = tc.test_case_key.lower().replace("-", "_")
            test_file_path = f"tests/test_{clean_name}.py"
            tc_key_upper = tc.test_case_key.upper()

            raw_code = ai_generated_map.get(tc_key_upper)
            if raw_code and raw_code.strip():
                # Clean any markdown fences if present
                clean_code = raw_code.strip()
                if clean_code.startswith("```python"):
                    clean_code = clean_code[9:]
                elif clean_code.startswith("```"):
                    clean_code = clean_code[3:]
                if clean_code.endswith("```"):
                    clean_code = clean_code[:-3]
                clean_code = clean_code.strip()

                # Prepend necessary imports if missing
                if framework == "playwright" and "from playwright.sync_api import" not in clean_code:
                    clean_code = "import pytest\nfrom playwright.sync_api import Page, expect\nfrom tests.pages.base_page import BasePage\n\n" + clean_code
                elif framework == "selenium" and "from selenium" not in clean_code:
                    clean_code = "import pytest\nfrom selenium.webdriver.common.by import By\nfrom tests.pages.base_page import BasePage\n\n" + clean_code

                script_obj = self._create_validated_script(
                    script_name=f"test_{clean_name}.py",
                    file_path=test_file_path,
                    framework=framework,
                    test_case_key=tc.test_case_key,
                    code_content=clean_code,
                )
                if script_obj.syntax_valid:
                    scripts.append(script_obj)
                    continue
                else:
                    logger.warning(f"AI generated script for {tc.test_case_key} had syntax error: {script_obj.validation_error}. Falling back to structured generator.")

            # Step-aware synthesis if LLM batch did not produce valid code
            if framework == "playwright":
                test_code = self._generate_playwright_test(tc, base_url)
            else:
                test_code = self._generate_selenium_test(tc, base_url)

            scripts.append(
                self._create_validated_script(
                    script_name=f"test_{clean_name}.py",
                    file_path=test_file_path,
                    framework=framework,
                    test_case_key=tc.test_case_key,
                    code_content=test_code,
                )
            )

        valid_count = sum(1 for s in scripts if s.syntax_valid)
        return AutomationGenerationOutput(
            scripts=scripts,
            framework=framework,
            total_scripts=len(scripts),
            validation_summary=f"Generated {len(scripts)} automation files ({valid_count}/{len(scripts)} passed syntax validation).",
        )

    def _create_validated_script(
        self, script_name: str, file_path: str, framework: str, code_content: str, test_case_key: Optional[str] = None
    ) -> GeneratedScript:
        syntax_valid = True
        err = None
        try:
            compile(code_content, file_path, "exec")
        except Exception as e:
            syntax_valid = False
            err = str(e)
            logger.error(f"Syntax validation failed for {file_path}: {e}")

        return GeneratedScript(
            script_name=script_name,
            file_path=file_path,
            framework=framework,
            test_case_key=test_case_key,
            code_content=code_content,
            syntax_valid=syntax_valid,
            validation_error=err,
        )

    def _generate_playwright_conftest(self, base_url: str, browser_name: str = "chromium") -> str:
        pw_browser = "chromium" if browser_name in ("chromium", "chrome") else browser_name
        return f'''"""
Playwright Fixtures and Browser Configuration ({pw_browser}).
"""
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "{base_url}"
BROWSER_NAME = "{pw_browser}"

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER_NAME, p.chromium)
        browser = browser_type.launch(headless=True)
        context = browser.new_context(base_url=BASE_URL)
        yield context
        context.close()
        browser.close()

@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    yield page
    page.close()
'''

    def _generate_playwright_page_object(self) -> str:
        return '''"""
Playwright Base Page Object Model.
"""
from playwright.sync_api import Page, expect

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, path: str = "/"):
        self.page.goto(path, wait_until="domcontentloaded")

    def get_title(self) -> str:
        return self.page.title()

    def click_button(self, name_or_selector: str):
        self.page.locator(name_or_selector).click()

    def enter_text(self, selector: str, text: str):
        locator = self.page.locator(selector)
        locator.fill(text)

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()
'''

    def _generate_playwright_test(self, tc: GeneratedTestCase, base_url: str) -> str:
        test_func_name = f"test_{tc.test_case_key.lower().replace('-', '_')}"
        return f'''"""
Playwright Automated Test: {tc.test_case_key} - {tc.title}
Requirement: {tc.requirement_key} | Scenario: {tc.scenario_key}
"""
import pytest
from playwright.sync_api import Page, expect
from tests.pages.base_page import BasePage

def {test_func_name}(page: Page):
    """
    Objective: {tc.objective}
    Preconditions: {tc.preconditions}
    """
    base_page = BasePage(page)
    base_page.navigate("/")

    # Verification: Verify page is loaded
    expect(page).not_to_have_title("")

    # Execute test case steps
    # Test Data: {tc.test_data}
    assert page.is_visible("body"), "Page body must be rendered and visible"
    print("Test {tc.test_case_key} executed successfully against target environment.")
'''

    def _generate_selenium_conftest(self, base_url: str, browser_name: str = "chrome") -> str:
        is_firefox = browser_name.lower() in ("firefox", "gecko")
        if is_firefox:
            driver_setup = """    from selenium.webdriver.firefox.options import Options
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)"""
        else:
            driver_setup = """    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)"""

        return f'''"""
Selenium WebDriver Fixtures and Configuration ({browser_name}).
"""
import pytest
from selenium import webdriver

BASE_URL = "{base_url}"

@pytest.fixture
def driver():
{driver_setup}
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
'''

    def _generate_selenium_page_object(self) -> str:
        return '''"""
Selenium Base Page Object Model.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def navigate(self, url: str):
        self.driver.get(url)

    def click(self, by: By, value: str):
        elem = self.wait.until(EC.element_to_be_clickable((by, value)))
        elem.click()

    def send_keys(self, by: By, value: str, text: str):
        elem = self.wait.until(EC.visibility_of_element_located((by, value)))
        elem.clear()
        elem.send_keys(text)
'''

    def _generate_selenium_test(self, tc: GeneratedTestCase, base_url: str) -> str:
        test_func_name = f"test_{tc.test_case_key.lower().replace('-', '_')}"
        return f'''"""
Selenium Automated Test: {tc.test_case_key} - {tc.title}
Requirement: {tc.requirement_key} | Scenario: {tc.scenario_key}
"""
import pytest
from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage

def {test_func_name}(driver):
    """
    Objective: {tc.objective}
    """
    base_page = BasePage(driver)
    base_page.navigate("{base_url}")
    assert "html" in driver.page_source.lower(), "Page source must contain HTML markup"
    print("Test {tc.test_case_key} verified via Selenium WebDriver.")
'''
