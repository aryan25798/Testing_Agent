# End-to-End Requirement Traceability Matrix (RTM)

This matrix establishes complete, bi-directional traceability from original business specifications down to automated test execution results.

---

## Traceability Table

| Requirement ID | Specification Source | Test Scenario ID | Scenario Title & Type | Test Case ID | Automated Script | Execution Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **REQ-001** | GitHub MCP (`aryan25798/TrainMate`) & Jira MCP (`KAN`) | **SCEN-001** | Verify Happy Path Standard Flow (Positive) | **TC-001** | `tests/test_tc_001.py` | Executed against `train-mate-blond.vercel.app` in 1.38s | **PASSED** |
| **REQ-001** | GitHub MCP (`aryan25798/TrainMate`) & Jira MCP (`KAN`) | **SCEN-002** | Verify Error Handling on Invalid Input (Negative) | **TC-002** | `tests/test_tc_002.py` | Executed against `train-mate-blond.vercel.app` in 1.30s | **PASSED** |
| **REQ-001** | GitHub MCP (`aryan25798/TrainMate`) & Jira MCP (`KAN`) | **SCEN-003** | Boundary & Character Limit Checks (Boundary) | **TC-003** | `tests/test_tc_003.py` | Executed against `train-mate-blond.vercel.app` in 1.40s | **PASSED** |
| **REQ-001** | GitHub MCP (`aryan25798/TrainMate`) & Jira MCP (`KAN`) | **SCEN-004** | Unauthorized Access & Session Expiry (Security) | **TC-004** | `tests/test_tc_004.py` | Executed against `train-mate-blond.vercel.app` in 1.35s | **PASSED** |

---

## Coverage Analysis

```text
Total Requirements:      1 (100% Covered)
Total Test Scenarios:    4 (100% Linked to Requirements)
Total Test Cases:        4 (100% Linked to Scenarios)
Automated Test Scripts:  4 Executable Suites + 2 Support Fixtures (100% Automated)
Execution Rate:          100% of Designed Cases Executed
Pass Rate:               100% (4 Passed, 0 Failed, 0 Blocked, 0 Skipped)
```
