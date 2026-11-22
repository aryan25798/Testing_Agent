"""
Dynamic Model Registry for Testing Agent Platform.
Discovers and caches available models across Gemini and OpenAI providers.
"""

from typing import List, Dict, Any, Optional
from src.llm.capabilities.models import KNOWN_CAPABILITIES, ModelCapability
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.openai_provider import OpenAIProvider
from src.core.logging import get_logger

logger = get_logger("model_registry")


class ModelRegistry:
    def __init__(self):
        self.gemini_provider = GeminiProvider()
        self.openai_provider = OpenAIProvider()
        self._cached_models: List[ModelCapability] = []
        self._is_initialized = False

    def set_credentials(self, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Updates provider credentials and refreshes available models."""
        if gemini_api_key:
            self.gemini_provider.set_api_key(gemini_api_key)
        if openai_api_key:
            self.openai_provider.set_api_key(openai_api_key)
        return self.refresh_models()

    def clear_credentials(self, provider: str):
        """Clears in-memory credentials for a provider and refreshes."""
        if provider.lower() == "gemini":
            self.gemini_provider.set_api_key("")
        elif provider.lower() == "openai":
            self.openai_provider.set_api_key("")
        return self.refresh_models()

    def refresh_models(self) -> List[ModelCapability]:
        """Discovers models from all configured providers and enriches with capabilities."""
        logger.info("Refreshing AI model registry...")
        discovered_models: List[ModelCapability] = []

        # Discover Gemini models
        try:
            gemini_list = self.gemini_provider.list_available_models()
            for m in gemini_list:
                mid = m["model_id"]
                known = KNOWN_CAPABILITIES.get(mid, {})
                discovered_models.append(
                    ModelCapability(
                        model_id=mid,
                        provider="gemini",
                        display_name=known.get("display_name", m.get("display_name", mid)),
                        context_window=known.get("context_window", 1000000),
                        supports_tools=known.get("supports_tools", True),
                        supports_structured_output=known.get("supports_structured_output", True),
                        supports_vision=known.get("supports_vision", False),
                        is_available=True,
                        cost_per_million_input_tokens=known.get("cost_in", 0.0),
                        cost_per_million_output_tokens=known.get("cost_out", 0.0),
                    )
                )
        except Exception as e:
            logger.error(f"Error fetching Gemini models: {e}")

        # Discover OpenAI models
        try:
            openai_list = self.openai_provider.list_available_models()
            for m in openai_list:
                mid = m["model_id"]
                known = KNOWN_CAPABILITIES.get(mid, {})
                discovered_models.append(
                    ModelCapability(
                        model_id=mid,
                        provider="openai",
                        display_name=known.get("display_name", m.get("display_name", mid)),
                        context_window=known.get("context_window", 128000),
                        supports_tools=known.get("supports_tools", True),
                        supports_structured_output=known.get("supports_structured_output", True),
                        supports_vision=known.get("supports_vision", False),
                        is_available=True,
                        cost_per_million_input_tokens=known.get("cost_in", 0.0),
                        cost_per_million_output_tokens=known.get("cost_out", 0.0),
                    )
                )
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")

        self._cached_models = discovered_models
        self._is_initialized = True
        logger.info(f"Model registry refreshed with {len(discovered_models)} models.")
        return self._cached_models

    def get_models(self) -> List[ModelCapability]:
        """Returns cached models or refreshes if empty."""
        if not self._is_initialized or not self._cached_models:
            return self.refresh_models()
        return self._cached_models

    def test_providers(self) -> Dict[str, bool]:
        """Tests live connectivity to Gemini and OpenAI."""
        return {
            "gemini": self.gemini_provider.test_connection(),
            "openai": self.openai_provider.test_connection(),
        }


model_registry = ModelRegistry()
