# Jira Cloud Integration Guide for Beginners

This visual guide walks you through connecting Jira to the Testing Agent Platform in under 2 minutes.

---

## 1. What You Need

1. **Jira Site URL**: e.g., `https://yourcompany.atlassian.net`
2. **Your Atlassian Email**: The email you use to sign into Jira.
3. **An Atlassian API Token**: A secure personal key (NEVER use your account password).

---

## 2. How to Generate an Atlassian API Token

1. Log into your Atlassian account at: [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**.
3. Label it `TestingAgentPlatform`.
4. Click **Create** and copy the generated token string.

---

## 3. Connecting in the Application

1. Open the Testing Agent Dashboard.
2. Navigate to **Settings ➔ Integrations ➔ Jira Integration** (or use Step 2 in the Guided Wizard).
3. Paste:
   - Your Jira Site URL
   - Your Email
   - Your API Token
4. Click **"Test Jira Connection"**.
5. Once connected, your projects and user stories will be automatically discovered.

---

## 4. Safety & Read-Only Guarantee

- The integration operates in **Read-Only** mode by default.
- It will never create, edit, close, transition, or comment on any Jira issue without explicit human approval.
