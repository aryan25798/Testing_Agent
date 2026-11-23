# System Inventory & Architectural Topology Report

**Document ID:** AUDIT-REP-01-SYSINV  
**Evaluation Status:** `PASS`  
**Evaluation Date:** 2026-11-23  
**Auditor:** Principal Software Architect & QA Automation Lead  
**Scope:** Complete End-to-End System Inventory (Frontend, Backend, Database, AI Agents, MCP, Sandbox)

---

## 1. Executive Summary

The AI Testing Assistant platform is an enterprise-grade autonomous quality engineering system. It autonomously translates software specifications (Jira stories, GitHub issues, PRDs) into boundary-exhaustive test scenarios, designs structured test cases, generates robust Page Object Model (POM) automation scripts in both Playwright and Selenium, and executes them in an isolated browser sandbox with live telemetry.

The platform has been unified under a single-port architecture where FastAPI serves both the high-performance async REST/SSE API and the compiled Angular 19 Single Page Application (SPA), completely eliminating the need for Node.js at runtime.

---

## 2. Full Repository Inventory & Directory Structure

```text
testing-agent-platform/
├── .env                              # Environment configuration (Encrypted keys, DB paths, CORS, Port)
├── .env.example                      # Production template for environment setup
├── .gitignore                        # Git exclusion rules (venv, artifacts, build outputs, SQLite databases)
├── pytest.ini                        # Pytest configuration (Strict asyncio mode, warning filters)
├── README.md                         # Comprehensive primary documentation (21 detailed chapters)
├── start.bat                         # Turnkey Windows 1-click launcher (Virtualenv, dependencies, browsers, server)
├── start.sh                          # Turnkey Linux/macOS 1-click launcher (Executable shell script)
├── requirements.txt                  # Python dependencies with strict version pinning
├── pyproject.toml                    # Python project metadata and build configuration
├── testing_platform.db               # SQLite database in WAL mode with AES-256 encrypted vault
│
├── frontend/                         # Angular 19 Production Single Page Application
│   ├── angular.json                  # Angular CLI build workspace configuration
│   ├── package.json                  # Node.js dependencies (Angular 19.2, RxJS 7.8, TailwindCSS)
│   ├── package-lock.json             # Immutable Node dependency lockfile
│   ├── tsconfig.json                 # TypeScript strict configuration
│   ├── tsconfig.app.json             # Application TypeScript compilation settings
│   ├── dist/                         # Compiled production distribution (Served by FastAPI)
│   │   └── frontend/browser/         # Static HTML, CSS, JS bundles (Initial total: 468.36 kB)
│   └── src/
│       ├── index.html                # Root HTML document
│       ├── main.ts                   # Angular application bootstrapping
│       ├── styles.css                # Global TailwindCSS and design system styles
│       └── app/
│           ├── app.component.ts      # Shell component with sidebar, status indicators, and modal triggers
│           ├── app.component.html    # Main layout template
│           ├── app.component.css     # App-level styling
│           ├── app.config.ts         # Angular application config with HTTP client and router
│           ├── app.routes.ts         # Client-side HTML5 PushState routes
│           ├── components/           # Feature components
│           │   ├── dashboard/        # Metrics overview and recent executions
│           │   ├── projects/         # Project catalog, creation modal, and configuration
│           │   ├── project-detail/   # Project management view with tabs
│           │   ├── workflow/         # LangGraph execution controller, live telemetry, and results
│           │   ├── scenarios/        # Test scenario review and generation grid
│           │   ├── test-cases/       # Test case designer and manual execution interface
│           │   ├── execution/        # Test execution runner, logs viewer, and defect pack export
│           │   ├── mcp-activity/     # Live MCP activity log viewer with filter by project
│           │   ├── approvals/        # Human-in-the-Loop approval requests management
│           │   ├── setup-wizard/     # One-click first-run setup modal for API keys
│           │   └── settings/         # Provider and model selector, agent configurations
│           ├── services/             # Angular injectable services
│           │   ├── api.service.ts    # Base HTTP service for backend communication
│           │   ├── workflow.service.ts # SSE telemetry stream handler and workflow runner
│           │   ├── project.service.ts # Project CRUD operations
│           │   ├── mcp.service.ts    # MCP activity and tool status
│           │   ├── approval.service.ts # HITL approval queue
│           │   └── setup.service.ts  # Setup status and key validation
│           └── models/               # TypeScript interfaces matching backend DTOs
│
├── src/                              # FastAPI Backend Source Code
│   ├── __init__.py                   # Package root
│   ├── main.py                       # FastAPI application entrypoint, lifespan manager, and SPA mount
│   ├── api/                          # REST API Routers
│   │   ├── projects_api.py           # Project CRUD and status endpoints
│   │   ├── scenarios_api.py          # Test scenario management and AI generation trigger
│   │   ├── test_cases_api.py         # Test case creation, update, and batch design
│   │   ├── execution_api.py          # Test runner trigger, log stream, and zip export
│   │   ├── workflows_api.py          # LangGraph orchestrator endpoints, SSE stream, and defect packs
│   │   ├── mcp_api.py                # MCP tools discovery and activity logs
│   │   ├── approvals_api.py          # HITL approval submission and decision endpoints
│   │   ├── models_api.py             # Model providers, key validation, and setup status
│   │   └── custom_agents_api.py      # Custom agent configurations and overrides
│   ├── agents/                       # Autonomous Quality Engineering AI Agents
│   │   ├── base_agent.py             # Abstract base agent with token budgeting and retry loops
│   │   ├── specification_analyst.py  # Agent 1: Spec parsing, Jira/GitHub ingestion, feature extraction
│   │   ├── test_planner.py           # Agent 2: Boundary analysis, risk matrix, test scenario planning
│   │   ├── test_case_designer.py     # Agent 3: Gherkin step design, pre/post conditions, assertions
│   │   ├── test_automation_engineer.py # Agent 4: Page Object Model code generation (Playwright/Selenium)
│   │   ├── test_executor.py          # Agent 5: Subprocess sandbox execution, assertion verification
│   │   └── quality_intelligence_lead.py # Agent 6: Flakiness scoring, coverage audit, sign-off gating
│   ├── core/                         # Core infrastructure and security utilities
│   │   ├── config.py                 # Pydantic BaseSettings, environment loading
│   │   ├── database.py               # SQLAlchemy engine, session maker, WAL pragma setup
│   │   ├── security/
│   │   │   ├── crypto_vault.py       # AES-256-GCM encryption for API keys and tokens
│   │   │   ├── audit_logger.py       # Tamper-evident structured audit logging
│   │   │   ├── prompt_sanitizer.py   # Indirect prompt injection filters and exfiltration guards
│   │   │   └── execution_sandbox.py  # OS subprocess runner with scrubbed environment
│   │   └── utils/
│   │       ├── json_repair.py        # Robust markdown fence stripper and JSON syntax repairer
│   │       └── token_limiter.py      # Sliding window token estimator and chunk batcher
│   ├── integrations/                 # External service integrations
│   │   ├── ai/                       # AI model providers
│   │   │   ├── provider_factory.py   # Multi-provider factory (Gemini, OpenAI, Mock)
│   │   │   ├── gemini_provider.py    # Google Gemini 2.0 Flash / 1.5 Pro implementation
│   │   │   └── openai_provider.py    # OpenAI GPT-4o / GPT-4o-mini implementation
│   │   ├── mcp/                      # Model Context Protocol
│   │   │   ├── mcp_client.py         # MCP JSON-RPC protocol client
│   │   │   ├── github_mcp.py         # GitHub MCP tools (issues, PRs, file contents)
│   │   │   ├── jira_mcp.py           # Jira MCP tools (stories, epics, comments)
│   │   │   └── approval_manager.py   # Human-in-the-Loop cryptographic approval queue
│   │   └── runners/                  # Automation execution runners
│   │       ├── playwright_runner.py  # Playwright async runner with screenshot capture
│   │       └── selenium_runner.py    # Selenium 4 runner with Chrome/Firefox drivers
│   ├── models/                       # SQLAlchemy ORM Entities
│   │   ├── base.py                   # DeclarativeBase with standard timestamps
│   │   └── entities.py               # Project, TestScenario, TestCase, TestExecution, Logs
│   ├── repositories/                 # Data Access Layer
│   │   ├── project_repository.py     # Project persistence operations
│   │   ├── scenario_repository.py    # Scenario persistence operations
│   │   ├── test_case_repository.py   # Test case persistence operations
│   │   └── execution_repository.py   # Execution logs and results persistence
│   ├── schemas/                      # Pydantic V2 Data Transfer Objects (DTOs)
│   │   └── dtos.py                   # Request/Response schemas with ConfigDict
│   ├── services/                     # Business Logic Services
│   │   ├── workflow_service.py       # LangGraph workflow orchestration and SSE events
│   │   ├── setup_service.py          # First-run wizard, key validation, environment saving
│   │   └── defect_export_service.py  # ZIP bundling service for screenshots and bug reports
│   └── workflows/                    # LangGraph Workflows
│       └── test_generation_workflow.py # 6-agent StateGraph pipeline with conditional routing
│
└── tests/                            # Comprehensive Automated Test Suite (38 tests)
    ├── conftest.py                   # Fixtures (in-memory SQLite, mock providers, test client)
    ├── test_crypto_vault.py          # AES-256-GCM encryption/decryption validation
    ├── test_prompt_sanitizer.py      # Prompt injection prevention tests
    ├── test_json_repair.py           # Malformed LLM output auto-repair tests
    ├── test_token_limiter.py         # Token windowing and batch chunking tests
    ├── test_mcp_integration.py       # MCP client and approval manager tests
    ├── test_runners.py               # Playwright and Selenium sandbox execution tests
    ├── test_agents.py                # 6 agents prompt generation and execution tests
    ├── test_langgraph_workflow.py    # End-to-end StateGraph execution flow tests
    ├── test_api_endpoints.py         # REST API route validation tests
    └── test_defect_export.py         # Defect bundle zip generation tests
```

---

## 3. Technology Stack Inventory

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Core** | FastAPI | 0.115.8+ | Async high-throughput REST API and SSE stream server |
| **Web Server** | Uvicorn | 0.34.0+ | ASGI production server |
| **Orchestration** | LangGraph | 0.2.70+ | Stateful multi-agent cyclic graph execution |
| **AI LLM Client** | Google GenAI / OpenAI SDK | Latest | Multi-model provider routing (Gemini 2.0 Flash, GPT-4o) |
| **Database** | SQLite3 | WAL Mode | Local embedded relational database with zero external ops |
| **ORM** | SQLAlchemy | 2.0.38+ | Typed relational mapping and schema management |
| **DTO / Validation** | Pydantic V2 | 2.10.6+ | Strict input/output schema validation and serialization |
| **Frontend Framework** | Angular | 19.2.0 | Modern component-based enterprise web interface |
| **Styling** | TailwindCSS | 3.4.0+ | Responsive utility-first design system |
| **Browser Engine** | Playwright & Selenium | 1.49+ / 4.28+ | Dual headless/headed browser automation execution |
| **Protocol** | Model Context Protocol (MCP) | Spec 2024-11 | Standardized external tool integration (GitHub & Jira) |
| **Cryptography** | PyCryptodome / Cryptography | 44.0.0+ | AES-256-GCM authenticated encryption for credential vault |
| **Testing** | Pytest / Pytest-Asyncio | 8.3.4+ / 0.25.3+ | Unit, integration, security, and E2E regression testing |

---

## 4. Verification Verdict

- **Total Architectural Modules:** 12 core backend modules, 11 frontend views, 6 autonomous agents.
- **Single-Port Consolidation:** Fully verified on `http://127.0.0.1:8000`.
- **System Inventory Status:** `PASS`.
