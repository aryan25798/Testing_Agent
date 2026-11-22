# Dynamic AI Model Engine & Per-Agent Configuration

The Testing Agent Platform features an independent, runtime-configurable model engine supporting both **Google Gemini** and **OpenAI**.

---

## 1. Supported Providers & Key Setup

Add your API keys to `.env`:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

Either provider can operate independently. If no key is configured, the system provides high-fidelity simulated fallback modes for local offline development.

---

## 2. Dynamic Model Discovery

Instead of relying on a hardcoded list, the platform queries provider APIs at runtime:
- **Gemini**: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash`, `gemini-1.5-pro`
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini`

Click **"Refresh Discovered Models"** in the UI (or call `POST /api/v1/models/refresh`) to detect newly released models.

---

## 3. Independent Per-Agent Model Selection

You can assign different models to each of the 6 agents based on cost, reasoning capability, or quota:

| Agent | Default Provider | Default Model | Best Suited For |
|---|---|---|---|
| **Agent 1: Requirement Analysis** | Gemini | `gemini-2.5-flash` | Fast document parsing and ambiguity detection |
| **Agent 2: Scenario Generation** | Gemini | `gemini-2.5-flash` | Broad scenario exploration & edge cases |
| **Agent 3: Test Case Design** | Gemini | `gemini-2.5-flash` | Step generation & synthetic test data |
| **Agent 4: Test Automation** | OpenAI | `gpt-4o-mini` | Precise code generation & Page Object Model |
| **Agent 5: Test Execution** | Gemini | `gemini-2.5-flash` | Log classification & root-cause analysis |
| **Agent 6: Reporting** | OpenAI | `gpt-4o-mini` | Executive summaries and coverage metrics |

---

## 4. Runtime Switching Without Restarting

You can switch models at any moment via:
1. **The Angular UI**: Under *AI Model Settings* (`/models`).
2. **The REST API**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/agents/agent_4_test_automation/switch-model \
        -H "Content-Type: application/json" \
        -d '{"provider": "gemini", "model_id": "gemini-2.5-pro"}'
   ```

Changing models does **NOT** restart the application or wipe previous execution checkpoints.
