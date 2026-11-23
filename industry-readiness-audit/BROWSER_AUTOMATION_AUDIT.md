# Browser Automation & Execution Sandbox Audit

**Document ID:** AUDIT-REP-08-BROWSER  
**Evaluation Status:** `PASS`  
**Evaluation Date:** 2026-11-23  
**Auditor:** QA Automation Lead & Sandbox Security Engineer  
**Scope:** Dual Framework Runners (Playwright & Selenium), POM Synthesis, Subprocess Isolation, Headed Watch Mode, and Defect Export Bundling

---

## 1. Executive Summary

The browser automation and execution infrastructure was audited for test framework fidelity, execution isolation, selector resilience, and defect artifact generation. The platform provides full dual-framework support for **Playwright** and **Selenium 4**, executing generated Page Object Model (POM) test suites within an isolated subprocess sandbox with scrubbed environments.

Engineers have access to a **Headed / Watch Mode toggle** to watch automated browser actions visually in real time, and a **Defect Evidence Bundle export** that packages all failure screenshots, reproduction guides, and execution logs into a client-ready ZIP archive.

---

## 2. Dual Framework Automation Architecture

```
                                  +------------------------------+
                                  | Test Automation Engineer     |
                                  | (Agent 4 POM Code Synthesis) |
                                  +--------------+---------------+
                                                 |
                       +-------------------------+-------------------------+
                       |                                                   |
                       v                                                   v
          +-------------------------+                         +-------------------------+
          |    Playwright Runner    |                         |     Selenium Runner     |
          |  Async Chromium/Firefox |                         |  Selenium 4 WebDriver   |
          +------------+------------+                         +------------+------------+
                       |                                                   |
                       +-------------------------+-------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | Execution Sandbox Subprocess |
                                  | - Scrubbed Host Environment  |
                                  | - 60s Timeout Watchdog       |
                                  | - Isolated Temporary Dir     |
                                  +--------------+---------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | Artifacts: Screenshots, Logs |
                                  | Defect Pack ZIP Export       |
                                  +------------------------------+
```

### 2.1 Playwright Implementation (`src/integrations/runners/playwright_runner.py`)
- **Execution Engine:** Async Playwright running pytest test suites.
- **Resilient POM Generation:** Generates discrete Page Classes with semantic locators (`page.get_by_test_id`, `page.get_by_role`, `page.locator`), avoiding brittle absolute XPaths.
- **Artifacts:** Captures high-resolution PNG screenshots on failure, full DOM snapshot logs, and timing metrics.

### 2.2 Selenium Implementation (`src/integrations/runners/selenium_runner.py`)
- **Execution Engine:** Selenium 4 WebDriver using modern `WebDriverWait` with `expected_conditions` (e.g. `element_to_be_clickable`, `visibility_of_element_located`).
- **Driver Management:** Automatically leverages modern Selenium Manager for driver binary discovery without requiring external chromedriver setup.
- **Artifacts:** Full-page screenshots on assertion failures and execution console logs.

---

## 3. Subprocess Execution Sandbox Security

### 3.1 Environment Scrubbing (`src/core/security/execution_sandbox.py`)
Executing dynamically synthesized code carries inherent security risks. The platform enforces strict OS subprocess isolation:
- **Environment Sanitization:** Before spawning the test runner subprocess, all sensitive host environment variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `CRYPTO_VAULT_KEY`, system tokens) are stripped from the child process environment.
- **Working Directory Isolation:** Subprocess runs in a sandboxed execution directory with restricted access to source code.
- **Timeout Watchdog:** Subprocesses are wrapped with an unyielding 60-second timeout. Rogue or hanging scripts are forcefully terminated (`SIGTERM` followed by `SIGKILL`) to prevent zombie processes.

---

## 4. Headed / Watch Mode & Enterprise Proxy Support

### 4.1 Headed / Watch Mode Toggle
Engineers can toggle between:
- **Headless Mode (Default):** Runs silently in the background, optimized for CI/CD pipelines and high speed.
- **Headed / Watch Mode:** Spawns a visible browser window directly on the desktop display:
  - Playwright: Passes `--headed` flag and slow-mo pacing.
  - Selenium: Omits `--headless` argument, initializing visible Chrome/Firefox window.
  - Enables testers to visually observe navigation, element interaction, and validation failures live.

### 4.2 Corporate Proxy & Staging Authentication Headers
The runners support testing applications located behind corporate VPNs and staging firewalls:
- Configurable `HTTP_PROXY` and `HTTPS_PROXY` injection.
- Injection of custom HTTP headers (e.g. `Authorization: Bearer <staging_token>`, `X-Bypass-Firewall: client_secret`) directly into the browser context.

---

## 5. Defect Evidence Pack ZIP Export

When tests fail, the platform compiles an enterprise defect pack via `GET /api/v1/workflows/project/{id}/export-zip`:
- **Contents of Exported Bundle:**
  - `README_REPRODUCTION.md`: Step-by-step reproduction instructions with Gherkin scenarios and expected vs. actual outcomes.
  - `QUALITY_AUDIT_REPORT.md`: Formal QA test execution report with pass/fail ratios and duration breakdowns.
  - `execution_manifest.json`: Machine-readable metadata linking test cases to error traces.
  - `screenshots/`: PNG failure screenshots capturing the exact visual state at the moment of assertion failure.
- **Delivery:** Generated dynamically in-memory using `zipfile.ZipFile` with `ZIP_DEFLATED` compression and streamed directly to the engineer's browser as `application/zip`.

---

## 6. Verification Verdict

- **Playwright Runner:** Verified and active.
- **Selenium Runner:** Verified and active.
- **Subprocess Isolation:** Verified with environment scrubbing in `tests/test_runners.py`.
- **Headed Mode Toggle:** Verified.
- **Defect Export ZIP:** Verified (HTTP 200 with valid zip structure).
- **Browser Automation Audit Status:** `PASS`.
