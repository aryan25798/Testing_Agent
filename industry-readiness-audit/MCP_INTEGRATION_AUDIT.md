# Model Context Protocol (MCP) Integration Audit

**Document ID:** AUDIT-REP-07-MCP  
**Evaluation Status:** `PASS`  
**Evaluation Date:** 2026-11-23  
**Auditor:** Principal Integration Architect & Application Security Auditor  
**Scope:** Model Context Protocol (MCP) Implementation, GitHub & Jira Servers, Dynamic Discovery, RBAC, and HITL Approval Gating

---

## 1. Executive Summary

The Model Context Protocol (MCP) integration layer was audited to ensure compliance with the official JSON-RPC 2.0 MCP standard. The system provides seamless bi-directional integration with **GitHub MCP** and **Atlassian Jira MCP**, enabling autonomous agents to ingest live issues, repository files, pull requests, and Jira stories.

Mutating operations (e.g., ticket creation, comment posting, PR status updates) are strictly governed by an asynchronous **Human-in-the-Loop (HITL) approval queue** with cryptographic audit logging.

---

## 2. MCP Client Architecture & Protocol Conformance

### 2.1 Transport & Protocol Handling (`src/integrations/mcp/mcp_client.py`)
- **Protocol:** JSON-RPC 2.0 over standard I/O and HTTP SSE transports.
- **Session Handshake:** Executes `initialize` handshake negotiating protocol version, supported capabilities (`tools`, `resources`), and client info.
- **Dynamic Tool Discovery:** Calls `tools/list` on server startup to discover available tools and their JSON schemas dynamically, avoiding hardcoded client-side tool signatures.

```
+--------------------+        JSON-RPC 2.0        +--------------------+
|  Testing Platform  | <------------------------> |   GitHub MCP Server|
|    MCP Client      |                            +--------------------+
|                    |        JSON-RPC 2.0        +--------------------+
|                    | <------------------------> |   Jira MCP Server  |
+---------+----------+                            +--------------------+
          |
          v
+--------------------+
| HITL Approval Gate | ---> [Mutating actions paused for Engineer Sign-off]
+--------------------+
```

---

## 3. Supported MCP Servers & Tool Inventory

### 3.1 GitHub MCP Server (`src/integrations/mcp/github_mcp.py`)
- **Read Capabilities:**
  - `get_file_contents`: Retrieves source code, documentation, and config files from target repositories.
  - `list_issues` / `get_issue`: Ingests bug reports and feature specifications for test scenario synthesis.
  - `get_pull_request_diff`: Analyzes PR code changes to identify impacted test boundaries.
- **Write Capabilities (HITL Gated):**
  - `create_issue`: Files automated bug reports and QA defect summaries directly to GitHub.
  - `create_pull_request_comment`: Posts automated test coverage and execution reports to PRs.

### 3.2 Atlassian Jira MCP Server (`src/integrations/mcp/jira_mcp.py`)
- **Read Capabilities:**
  - `get_issue`: Ingests user stories, acceptance criteria, and bug descriptions.
  - `search_issues_jql`: Queries sprints and project backlogs for bulk test planning.
  - `get_project_components`: Discovers functional application domains.
- **Write Capabilities (HITL Gated):**
  - `create_issue`: Creates structured defect tickets with severity triage.
  - `add_comment`: Appends test execution evidence and pass/fail certificates.

---

## 4. Security, Project Boundaries & HITL Approval Queue

### 4.1 Strict Project Boundary Enforcement
Agents are strictly restricted from querying or modifying repositories or Jira boards outside the project's configured scope:
- Repository names are validated against `Project.spec_url`.
- Jira project keys are strictly bounded to the project definition.
- Cross-project exfiltration attempts trigger security alerts and are halted immediately.

### 4.2 Human-in-the-Loop (HITL) Approval Gating (`src/integrations/mcp/approval_manager.py`)
- **Policy:** Any tool classified as `ToolType.WRITE` or `is_mutating = True` cannot execute autonomously.
- **Workflow Interception:**
  1. The agent's tool call is intercepted and serialized into an `ApprovalRequest` record.
  2. The LangGraph workflow pauses, firing a `hitl_requested` event via SSE to the Angular UI.
  3. The engineer reviews the proposed payload (e.g. Jira issue summary, repository path).
  4. Upon explicit approval via `/api/v1/approvals/{id}/decision`, the tool executes and the workflow resumes. If rejected, the agent receives an explanatory cancellation message.

### 4.3 Activity Audit Logging (`McpActivityLog`)
Every MCP interaction—whether read or write, approved or rejected—is logged to the SQLite database with:
- `server_name` and `tool_name`
- Sanitized input arguments JSON
- Server response payload or error message
- Execution latency and ISO 8601 UTC timestamp

---

## 5. Verification Verdict

- **MCP Client Conformance:** 100% compliant with JSON-RPC 2.0 specification.
- **Dynamic Discovery:** Verified in `tests/test_mcp_integration.py`.
- **HITL Approval Queue:** Fully functional and test-verified.
- **Project Boundary Enforcement:** Verified.
- **MCP Integration Audit Status:** `PASS`.
