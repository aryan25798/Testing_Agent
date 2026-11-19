# Git Repository Integration Guide

Connect GitHub, GitLab, Bitbucket, or Azure DevOps to automatically detect existing testing frameworks, page objects, and repository structure.

---

## 1. Supported Providers

- **GitHub** (Cloud & Enterprise)
- **GitLab** (Cloud & Self-Hosted)
- **Bitbucket**
- **Azure DevOps**

---

## 2. Generating a Personal Access Token (PAT)

### GitHub:
1. Go to `Settings` ➔ `Developer settings` ➔ `Personal access tokens` ➔ `Tokens (classic)`.
2. Generate a token with `repo:read` permission (read-only access to repository contents).
3. Copy the token.

---

## 3. How the Agent Uses Git

1. **Framework Discovery**: Automatically detects whether your repo already uses `pytest`, `playwright`, or `selenium`.
2. **Page Object Discovery**: Scans for existing page models so generated tests seamlessly reuse your existing locators.
3. **Strict Read-Only Default**: The platform will **NEVER** commit, push, or open pull requests automatically. All proposed file changes are displayed for explicit user approval first.
