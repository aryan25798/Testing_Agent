# AI Testing Assistant Architecture

This document provides a technical overview of the enterprise architecture powering the AI-powered Software Testing Platform.

---

## 1. High-Level Architecture

```
+-----------------------------------------------------------------------------------------+
|                                 Angular Frontend (UI)                                   |
|   - Executive KPI Cards          - ECharts Trend / Donut Gauges - 6-Agent Flow Monitor  |
|   - Test Cases & Execution Grid  - MCP Integration Center       - Model Router Controls |
+--------------------------------------------+--------------------------------------------+
                                             | HTTP / REST
+--------------------------------------------v--------------------------------------------+
|                                  FastAPI Core Backend                                   |
|   - /projects    - /requirements    - /scenarios    - /test-cases                       |
|   - /automation  - /executions      - /models       - /workflows                        |
+--------------------------------------------+--------------------------------------------+
                                             |
         +-----------------------------------+-----------------------------------+
         |                                                                       |
+--------v-----------------------------------+               +-------------------v--------+
|       LangGraph 6-Agent State Machine      |               |  Dynamic AI Model Engine   |
|                                            |               |                            |
| 1. Requirement Analysis Agent              |               |  - Gemini Provider         |
| 2. Test Scenario Generation Agent          |               |  - OpenAI Provider         |
| 3. Test Case Design Agent                  | <-----------> |  - Dynamic Model Discovery |
| 4. Test Automation Agent (Playwright/POM)  |               |  - Capability Detection    |
| 5. Test Execution Agent (Isolated Runner)  |               |  - Per-Agent Model Routing |
| 6. Orchestration & Reporting Agent         |               |  - Runtime Model Switching |
+--------------------+-----------------------+               +----------------------------+
                     |
+--------------------v-----------------------+
|        Storage & Integrations              |
|  - SQLite (Local) / PostgreSQL (Prod)      |
|  - Jira Cloud REST API (Read-only default) |
|  - Git Inspection (GitHub / GitLab / ADO)  |
|  - Document Parsers (PDF, Word, Excel, CSV)|
|  - Sandboxed Python Test Runner            |
+--------------------------------------------+
```

---

## 2. The 6-Agent LangGraph Workflow

The testing lifecycle is managed as an asynchronous state graph:

1. **Agent 1: Requirement Analysis Agent**
   - Inputs: User stories, acceptance criteria, PRDs (Jira, PDF, Word, Excel, CSV, Text).
   - Validations: Enforces that missing business requirements are never fabricated; records clarification questions.
2. **Agent 2: Test Scenario Generation Agent**
   - Generates positive, negative, boundary, equivalence partitioning, security, and edge-case scenarios with requirement traceability.
3. **Agent 3: Test Case Design Agent**
   - Generates executable step-by-step test cases and synthetic test data (PII protected).
4. **Agent 4: Test Automation Agent**
   - Writes production-grade Python scripts using Playwright or Selenium following Page Object Model (POM). Validates syntax before saving.
5. **Agent 5: Test Execution & Validation Agent**
   - Runs tests inside isolated temporary subprocesses, captures logs and execution duration, and classifies failures (`ApplicationDefect`, `EnvironmentIssue`, `FlakyTest`).
6. **Agent 6: Test Orchestration & Reporting Agent**
   - Enforces approval gates, calculates requirement and automation coverage, and compiles consolidated reports in Markdown, JSON, CSV, and PDF.

---

## 3. Database Schema

- `projects`: Application records and framework preferences.
- `requirements`: Extracted and approved requirements.
- `test_scenarios`: Traceable testing scenarios.
- `test_cases`: Actionable step-by-step test cases with synthetic test data.
- `automation_scripts`: Executable Python scripts.
- `test_executions`: Test suite runs and metadata.
- `test_execution_results`: Detailed status, error message, and failure classifications.
- `approval_requests`: Human-in-the-loop decisions and audit history.
- `agent_executions`: Token consumption and latency tracking per agent.
