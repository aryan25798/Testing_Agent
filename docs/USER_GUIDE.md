# Beginner User Guide: AI Testing Assistant

This guide explains the dashboard, the 6 AI testing agents, and key software testing concepts in simple, plain English.

---

## 1. Dashboard Overview

The main dashboard answers 5 simple questions:

1. **What project am I testing?** (Displayed in the sidebar project selector)
2. **What is the current status?** (Top KPI cards: Test Suites, Run History, Success Rate)
3. **What passed and what failed?** (Test Results Overview donut chart)
4. **Is our quality improving over time?** (Execution Trend line chart)
5. **What requires my attention?** (Test Suites Overview table and live Recent Activity feed)

---

## 2. Plain-English QA Glossary for Freshers

- **Requirement**: A statement describing what a feature should do (e.g., *"Users can reset password with an email link"*).
- **Acceptance Criteria**: The checklist of conditions that must be satisfied for a feature to be considered done.
- **Test Scenario**: A high-level situation that needs to be checked (e.g., *"Verify checkout when card has insufficient balance"*).
- **Test Case**: The exact step-by-step instructions (Click button A, Type B, Expect C).
- **Synthetic Test Data**: Fake generated test records (like `user123@example.com`) used safely so real customer private information is never compromised.
- **Automation Script**: A Python program that controls a web browser to test your site automatically.
- **Playwright & Selenium**: Tools that let computers interact with websites just like a real person.
- **Test Execution**: Actually running the tests to see if the website behaves correctly.
- **Requirement Coverage**: The percentage of your business requirements that have tests written for them.
- **Automation Coverage**: The percentage of your test cases that run automatically without human clicking.

---

## 3. The 6 Specialized Testing Agents

| Agent | Name | What It Does For You |
|---|---|---|
| **Agent 1** | Requirement Analysis Agent | Reads your documents/Jira, finds acceptance criteria, and flags missing information without making up fake requirements. |
| **Agent 2** | Test Scenario Generation Agent | Creates balanced positive, negative, boundary, and security test situations. |
| **Agent 3** | Test Case Design Agent | Writes detailed steps and generates safe synthetic test data. |
| **Agent 4** | Test Automation Agent | Writes clean Python Playwright or Selenium code following the Page Object Model pattern. |
| **Agent 5** | Test Execution Agent | Runs test scripts in an isolated sandbox and explains why any test failed. |
| **Agent 6** | Orchestration & Reporting Agent | Coordinates the team, ensures safety gates, calculates coverage, and builds PDF/CSV reports. |
