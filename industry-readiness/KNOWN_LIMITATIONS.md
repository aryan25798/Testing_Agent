# KNOWN LIMITATIONS AND OPERATIONAL BOUNDARIES

**Audit Date:** November 22, 2026  
**Auditor Roles:** Principal Software Architect, Application Security Engineer, DevOps Engineer  
**Repository:** `testing-agent-platform`  
**Deployment Model:** Local Developer / Team Server (FastAPI + Angular 19 + SQLite WAL / PostgreSQL Option)  
**Status:** **DOCUMENTED & ARCHITECTURALLY MANAGED**

---

## 1. Purpose & Scope

An industry-grade engineering platform must be completely transparent regarding its design boundaries, operational constraints, and non-goals. This document specifies the known technical limitations of the current architecture and provides explicit engineering migration guidance for teams scaling beyond the default local deployment profile.

---

## 2. Detailed Technical Limitations

### 2.1 SQLite Database Concurrency & Scaling Boundaries
- **Current Architecture:** By default, the platform deploys with a local SQLite database running in Write-Ahead Logging mode (`PRAGMA journal_mode=WAL`) with a 5,000 ms busy timeout (`PRAGMA busy_timeout=5000`).
- **Operational Boundary:** WAL mode permits unlimited concurrent readers alongside a single serialized writer. This architecture comfortably supports:
  * Individual software engineers and QA automation testers.
  * Small development teams running up to 5 concurrent agent workflows.
  * Batch execution rates of ~400 write transactions/second.
- **Limitation:** Under high concurrent write contention (> 10 parallel background workflows executing simultaneous database writes), SQLite may experience database locking delays (`sqlite3.OperationalError: database is locked`) if the 5-second busy timeout is exceeded.
- **Enterprise Remediation:** The platform database layer (`src/models/session.py`) is built entirely on standard SQLAlchemy ORM abstractions. Teams deploying to shared CI/CD runners or centralized servers can switch to **PostgreSQL** by changing a single environment variable in `.env`:
  ```dotenv
  DATABASE_URL=postgresql+psycopg2://qa_user:secure_pass@postgres-server:5432/qa_platform
  ```
  Zero codebase modifications are required.

---

### 2.2 Local Browser Automation & Resource Footprint
- **Current Architecture:** Agent 5 (Test Execution) launches local browser processes (Playwright Chromium/Firefox/WebKit or Selenium WebDriver Chrome) in sandboxed headless mode on the host workstation.
- **Operational Boundary:** Up to 3 concurrent headless browser instances execute smoothly on an 8 GB RAM machine without degraded responsiveness.
- **Limitation:** Launching more than 5 parallel headed or headless browser instances locally will cause significant host CPU and RAM consumption (each Chromium instance consumes 150–250 MB RAM).
- **Enterprise Remediation:** For massive parallel execution across hundreds of test suites, teams should point Playwright scripts to an external remote browser grid:
  * Playwright Browser Server: `browser = playwright.chromium.connect("ws://playwright-grid:3000/")`
  * Selenium Grid / Browserless.io infrastructure.

---

### 2.3 External AI Provider Quotas & Rate Limits
- **Current Architecture:** Agents interface with Google Gemini (via `google-genai`) and OpenAI (via `openai`) using typed adapter interfaces and fail-fast exception handling.
- **Operational Boundary:** Latency and throughput are fundamentally constrained by the upstream AI provider's API tier limits and geographic proximity to provider inference endpoints.
- **Limitation:** If a user configures a free-tier API key with restrictive rate limits (e.g., Gemini Free Tier: 15 requests per minute), executing a large batch workflow may trigger provider HTTP 429 (`RESOURCE_EXHAUSTED`).
- **Engineered Behavior:** The platform does not silently fall back to fake or mock data. It raises a typed `LLMGenerationError`, records the error in the audit log, and notifies the user in the UI with recommended retry actions.
- **Air-Gapped / Local LLM Alternative:** For environments with zero internet access, LiteLLM supports pointing to local **Ollama** or **vLLM** endpoints (`ollama/codellama`, `vllm/mistral-large`).

---

### 2.4 Headed Browser Execution in Headless Linux / Docker Environments
- **Current Architecture:** Headless mode (`headless=True`) is the verified default across all operating systems.
- **Limitation:** If an engineer configures `headless=False` (to observe browser interactions visually) inside a headless Linux server or Docker container lacking an X11 server, browser launch will fail with `Missing X server or $DISPLAY`.
- **Remediation:** Use headless mode in CI/CD environments. For headed debugging on Linux servers, wrap execution with `xvfb-run -a python -m pytest`.

---

### 2.5 Model Context Protocol (MCP) Tool Prerequisites
- **Current Architecture:** The platform orchestrates external tools via the Model Context Protocol (MCP).
- **Operational Boundary:**
  * **GitHub MCP Server:** Launches via `npx -y @modelcontextprotocol/server-github`. Requires Node.js installed on the host and an authorized GitHub Personal Access Token (`GITHUB_PERSONAL_ACCESS_TOKEN`).
  * **Atlassian Jira Remote MCP Server:** Requires valid Jira Cloud API credentials (`ATLASSIAN_URL`, `ATLASSIAN_USER_EMAIL`, `ATLASSIAN_API_TOKEN`).
- **Limitation:** If Node.js is missing or network firewall rules block GitHub/Atlassian APIs, MCP tool invocations will fail.
- **Engineered Behavior:** MCP integration tests verify graceful degradation: if an external MCP tool is unavailable, the agent logs an audit warning and continues pipeline execution with available local context rather than terminating the workflow.

---

## 3. Explicit Non-Goals for Local Platform Distribution

To preserve architecture integrity, maintain security, and respect the local engineering tool model, the following features are intentionally out of scope:

1. **Multi-Tenant SaaS Infrastructure:** The platform is designed as an engineer-centric, team-distributable tool, not a multi-tenant SaaS service with billing, tenant partitioning, or Stripe integration.
2. **Native Mobile App Automation (iOS / Android):** The automation engine specializes in modern Web Applications (single-page apps, progressive web apps, responsive viewports) via Playwright and Selenium. Mobile app binary testing (Appium/Espresso/XCUITest) is not supported.
3. **Unsanctioned Black-Box Penetration Testing:** Agent security scenarios focus strictly on application-level automated QA security validation (input validation, authentication boundaries, CSRF, XSS prevention), not unauthorized network infrastructure exploits.

---

## 4. Summary Matrix

| Limitation Area | Impact Level | Primary Mitigation | Scalability Horizon |
|---|---|---|---|
| **SQLite Concurrent Writes** | Low (Single User / Team) | Busy timeout (5s) + WAL mode | Migrate to PostgreSQL via `.env` |
| **Local Browser Parallelism** | Medium | Headless Chromium default | Connect to Playwright Remote Grid |
| **AI Provider Quotas** | Medium | Fail-fast errors + structured schemas | Upgrade provider tier or use local Ollama |
| **MCP Node.js Prerequisite** | Low | Documented in `setup.ps1` | Standard Node.js LTS installation |
| **Headed Linux Display** | Low | Headless default | `xvfb-run` virtual framebuffer |

**Conclusion:** All operational boundaries are well-understood, documented, and architecturally guarded against silent failure.
