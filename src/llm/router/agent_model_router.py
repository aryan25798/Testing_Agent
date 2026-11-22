"""
Per-Agent Model Router and Runtime Switching Engine.
Maintains independent model configuration for all 6 specialized testing agents.
"""

from typing import Dict, Any, Optional, Tuple
from src.llm.providers.base import BaseLLMProvider
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.openai_provider import OpenAIProvider
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger("agent_model_router")

AGENT_METADATA = {
    "agent_1_requirement_analysis": {
        "name": "Requirement Analysis Agent",
        "description": "Extracts functional, non-functional, business rules, and acceptance criteria.",
        "default_provider": "gemini",
        "default_model": "gemini-2.5-flash",
    },
    "agent_2_scenario_generation": {
        "name": "Test Scenario Generation Agent",
        "description": "Generates positive, negative, boundary, and edge-case test scenarios.",
        "default_provider": "gemini",
        "default_model": "gemini-2.5-flash",
    },
    "agent_3_test_case_design": {
        "name": "Test Case Design Agent",
        "description": "Designs executable step-by-step test cases with synthetic test data.",
        "default_provider": "gemini",
        "default_model": "gemini-2.5-flash",
    },
    "agent_4_test_automation": {
        "name": "Test Automation Agent",
        "description": "Converts approved test cases into Selenium or Playwright Python scripts.",
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
    },
    "agent_5_test_execution": {
        "name": "Test Execution & Validation Agent",
        "description": "Executes automated tests in isolated sandboxes and classifies failures.",
        "default_provider": "gemini",
        "default_model": "gemini-2.5-flash",
    },
    "agent_6_orchestration_reporting": {
        "name": "Test Orchestration & Reporting Agent",
        "description": "Coordinates lifecycle gates, calculates coverage metrics, and builds reports.",
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
    },
}


class AgentModelRouter:
    def __init__(self):
        self.gemini_provider = GeminiProvider()
        self.openai_provider = OpenAIProvider()
        self._agent_configs: Dict[str, Dict[str, str]] = {}

        # Initialize defaults
        for agent_id, meta in AGENT_METADATA.items():
            self._agent_configs[agent_id] = {
                "provider": meta["default_provider"],
                "model_id": meta["default_model"],
            }

    def set_credentials(self, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Updates provider instances with new API keys."""
        if gemini_api_key:
            self.gemini_provider.set_api_key(gemini_api_key)
        if openai_api_key:
            self.openai_provider.set_api_key(openai_api_key)

    def get_agent_config(self, agent_id: str) -> Dict[str, str]:
        """Returns the current provider and model configuration for a given agent."""
        if agent_id not in self._agent_configs:
            # Fallback to global defaults
            return {
                "provider": settings.DEFAULT_PROVIDER,
                "model_id": settings.DEFAULT_GEMINI_MODEL if settings.DEFAULT_PROVIDER == "gemini" else settings.DEFAULT_OPENAI_MODEL,
            }
        return self._agent_configs[agent_id]

    def set_agent_model(self, agent_id: str, provider: str, model_id: str) -> Dict[str, str]:
        """Switches an agent's AI model at runtime without restarting or losing workflow history."""
        clean_provider = provider.lower()
        if clean_provider not in ["gemini", "openai"]:
            raise ValueError(f"Unsupported AI provider: {provider}")

        self._agent_configs[agent_id] = {
            "provider": clean_provider,
            "model_id": model_id,
        }
        logger.info(f"Switched model for {agent_id} -> {clean_provider} / {model_id}")
        return self._agent_configs[agent_id]

    def get_provider_and_model(self, agent_id: str) -> Tuple[BaseLLMProvider, str]:
        """Returns the active provider instance and target model ID for an agent."""
        config = self.get_agent_config(agent_id)
        provider_name = config["provider"]
        model_id = config["model_id"]

        if provider_name == "gemini":
            return self.gemini_provider, model_id
        elif provider_name == "openai":
            return self.openai_provider, model_id
        else:
            return self.gemini_provider, model_id

    def get_all_configurations(self) -> Dict[str, Any]:
        """Returns full overview of all agents and their active model configuration."""
        result = {}
        for agent_id, meta in AGENT_METADATA.items():
            current = self.get_agent_config(agent_id)
            result[agent_id] = {
                "agent_id": agent_id,
                "name": meta["name"],
                "description": meta["description"],
                "provider": current["provider"],
                "model_id": current["model_id"],
            }
        return result


agent_model_router = AgentModelRouter()
