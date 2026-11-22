# Application Security & Zero-Exposure Audit

**Audit Objective:** Verify that testing workflows, subprocess sandboxes, and MCP connections strictly comply with enterprise security constraints.

---

## 1. Credential Vault Verification (AES-256-GCM)
* **Storage Location:** `secrets_manager.py` manages encryption keys and encrypted secret payloads at rest.
* **Network Exposure:** The frontend Angular application receives only sanitized status indicators (`connected`, `tools_count`). Plaintext PATs and API keys are never exposed in browser cookies, session storage, or DOM attributes.

---

## 2. MCP Subprocess Isolation & Mutating Tool Interception
* **Execution Boundary:** `@modelcontextprotocol/server-github` and `mcp-atlassian` run as child subprocesses over standard I/O (`stdio`).
* **Mutating Tool Gate:** High-risk actions (`create_pull_request`, `push_files`, `create_issue`, `jira_create_issue`) are assigned a `high` risk level in `tool_registry.py`. When an agent invokes them, execution is intercepted, an approval ticket is created, and execution halts until an authorized engineer clicks **Approve** in the UI.

---

## 3. Test Automation Execution Sandbox Security
* **Environment Scrubbing:** Before launching Playwright automation scripts, the environment dictionary is filtered. Keys matching `*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*`, `*DATABASE*`, `*GEMINI*`, `*OPENAI*`, `*GITHUB*`, or `*JIRA*` are purged.
* **Process Confinement:** Untrusted AI-generated scripts never execute in the FastAPI main thread. They run in a separate subprocess with an enforced 30-second timeout to prevent denial-of-service loops.
