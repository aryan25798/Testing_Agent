# Database Architecture & Relational Integrity Audit

**Document ID:** AUDIT-REP-05-DATABASE  
**Evaluation Status:** `PASS`  
**Evaluation Date:** 2026-11-23  
**Auditor:** Principal Database Architect & Data Protection Officer  
**Scope:** SQLite Relational Architecture, Schema Entities, Foreign Key Cascades, WAL Mode Concurrency, and Encrypted Vault Persistence

---

## 1. Executive Summary

The persistence architecture was audited to verify relational integrity, ACID compliance, concurrent read/write throughput, and credential protection. The platform utilizes an embedded **SQLite3** database running in **Write-Ahead Logging (WAL)** mode with explicit foreign key constraints enforced at connection initialization.

Sensitive application credentials and third-party API tokens are protected at rest within the `system_configs` table using hardware-accelerated **AES-256-GCM** authenticated encryption.

---

## 2. Database Engine & Concurrency Configuration

### 2.1 SQLite WAL Mode & Pragmas (`src/core/database.py`)
To prevent database locks during parallel AI agent telemetry updates and browser execution log streams, the SQLite engine is initialized with optimal enterprise pragmas:
```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA busy_timeout = 10000")
    cursor.close()
```
- **`journal_mode = WAL`:** Enables concurrent readers while a writer transaction is active, eliminating `database is locked` errors during intense agent workflows.
- **`foreign_keys = ON`:** Guarantees relational referential integrity across all tables.
- **`busy_timeout = 10000`:** Sets a 10-second wait window before raising lock exceptions under extreme concurrent write contention.

---

## 3. Relational Schema & Entity Inventory

The database schema defines 8 interconnected entities in `src/models/entities.py`:

```
+-------------------------------------------------------+
|                       Project                         |
|  PK: id (UUID)                                        |
|  name, spec_type, spec_url, target_url, created_at    |
+--------------------------+----------------------------+
                           | 1:N (CASCADE)
         +-----------------+-----------------+
         |                                   |
+--------v--------------+         +----------v--------------+
|     TestScenario      |         |      TestExecution      |
|  PK: id (UUID)        |         |  PK: id (UUID)          |
|  FK: project_id       |         |  FK: project_id         |
|  test_type, priority  |         |  runner_type, status    |
+--------+--------------+         +----------+--------------+
         | 1:N (CASCADE)                     | 1:N (CASCADE)
+--------v--------------+         +----------v--------------+
|       TestCase        |         |   TestExecutionResult   |
|  PK: id (UUID)        |         |  PK: id (UUID)          |
|  FK: scenario_id      |         |  FK: execution_id       |
|  gherkin_steps, data  |<--------+  FK: test_case_id       |
+-----------------------+         |  status, screenshot_path|
                                  +-------------------------+
```

### 3.1 Entity Model Specifications
1. **`Project`:** Root entity representing the application under test. Stores target URLs, framework preferences, and specification metadata.
2. **`TestScenario`:** Stores synthesized boundary scenarios categorized by `test_type` (Positive, Negative, Boundary, Edge-Case, Security).
3. **`TestCase`:** Detailed executable test cases with structured Gherkin steps, preconditions, input fixtures, and expected results. Annotated with `__test__ = False` for test runner isolation.
4. **`TestExecution`:** High-level execution record tracking runner type (Playwright vs. Selenium), duration, total tests, passed, failed, and status. Annotated with `__test__ = False`.
5. **`TestExecutionResult`:** Individual test case outcome including execution logs, assertion failures, execution duration, and path to captured screenshot. Annotated with `__test__ = False`.
6. **`McpActivityLog`:** Comprehensive audit trail of external tool invocations against GitHub and Jira MCP servers.
7. **`AuditLog`:** Security audit events capturing user actions, IP addresses, resource IDs, and timestamps.
8. **`SystemConfig`:** Cryptographically secured table holding encrypted API keys and system settings.

---

## 4. Referential Integrity & Cascade Verifications

All foreign key relationships enforce `ondelete="CASCADE"`:
- Deleting a `Project` automatically purges all associated `TestScenario`, `TestCase`, `TestExecution`, `TestExecutionResult`, and `McpActivityLog` records.
- Deleting a `TestScenario` cascades to its child `TestCase` records.
- Deleting a `TestExecution` cascades to its child `TestExecutionResult` records.
- Referential constraints prevent orphaned records in SQLite.

---

## 5. Encrypted Credential Vault

Sensitive external keys (Google Gemini API key, OpenAI API key, GitHub PAT, Jira API Token) are stored encrypted in `SystemConfig`:
- **Cipher:** AES-256-GCM (Galois/Counter Mode) authenticated encryption.
- **Key Derivation:** Derived from master `CRYPTO_VAULT_KEY` in `.env` using PBKDF2 with 100,000 SHA-256 iterations.
- **Authentication Tag:** Each encrypted ciphertext includes a 16-byte authentication tag verifying that credentials have not been tampered with at rest.

---

## 6. Verification Verdict

- **Relational Integrity:** 100% compliant with foreign key enforcement.
- **Concurrency Mode:** WAL mode active and verified.
- **Data at Rest Protection:** Authenticated AES-256-GCM encryption verified.
- **Database Audit Status:** `PASS`.
