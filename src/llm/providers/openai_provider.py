"""
OpenAI Provider Adapter.
Supports dynamic model discovery, text generation, and JSON schema outputs.
"""

import time
import json
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
from src.llm.providers.base import BaseLLMProvider, LLMResponse
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger("openai_provider")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            try:
                from src.core.security.secrets_manager import secrets_manager
                api_key = secrets_manager.get_secret("openai") or secrets_manager.get_secret("openai_api_key")
            except Exception:
                pass
        super().__init__(api_key=api_key or settings.OPENAI_API_KEY)
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def set_api_key(self, api_key: str):
        """Updates API key and re-initializes client dynamically."""
        self.api_key = api_key
        self._init_client()

    def test_connection(self) -> bool:
        if not self.api_key or not self._client:
            return False
        try:
            self._client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def list_available_models(self) -> List[Dict[str, Any]]:
        default_openai_models = [
            {"model_id": "gpt-4o", "display_name": "GPT-4o (gpt-4o)", "context_window": 128000},
            {"model_id": "gpt-4o-mini", "display_name": "GPT-4o Mini (gpt-4o-mini)", "context_window": 128000},
            {"model_id": "o1", "display_name": "o1 Reasoning (o1)", "context_window": 200000},
            {"model_id": "o3-mini", "display_name": "o3 Mini (o3-mini)", "context_window": 200000},
        ]
        if not self._client:
            return default_openai_models

        try:
            discovered = []
            res = self._client.models.list()
            for m in res.data:
                mid = m.id
                lower_id = mid.lower()
                # Exclude embeddings, audio, tts, whisper, moderation, realtime
                if any(x in lower_id for x in ["embedding", "tts", "whisper", "dall-e", "moderation", "realtime", "babbage", "davinci"]):
                    continue
                # Include chat and reasoning models
                if lower_id.startswith("gpt-") or lower_id.startswith("o1") or lower_id.startswith("o3") or lower_id.startswith("chatgpt"):
                    discovered.append({
                        "model_id": mid,
                        "display_name": f"{mid.replace('-', ' ').title()} ({mid})",
                        "context_window": 128000,
                    })
            discovered.sort(key=lambda x: x["model_id"])
            return discovered if discovered else default_openai_models
        except Exception as e:
            logger.warning(f"Failed to retrieve OpenAI models list: {e}. Using catalog.")
            return default_openai_models

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_OPENAI_MODEL
        start_time = time.time()

        if self._client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self._client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency = time.time() - start_time
                text = response.choices[0].message.content or ""
                in_tokens = response.usage.prompt_tokens if response.usage else len(prompt.split())
                out_tokens = response.usage.completion_tokens if response.usage else len(text.split())

                return LLMResponse(
                    text=text,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    latency_seconds=round(latency, 2),
                    model=target_model,
                    provider="openai",
                )
            except Exception as e:
                logger.error(f"OpenAI generate_text failed: {e}")

        # Fallback simulation
        latency = time.time() - start_time
        return LLMResponse(
            text=f"[Simulated OpenAI Output for: {prompt[:80]}...]",
            input_tokens=len(prompt.split()),
            output_tokens=50,
            latency_seconds=round(latency, 2),
            model=target_model,
            provider="openai",
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_OPENAI_MODEL
        start_time = time.time()

        if self._client:
            try:
                messages = []
                system_text = (system_prompt or "") + "\nYou MUST return valid JSON."
                messages.append({"role": "system", "content": system_text})
                messages.append({"role": "user", "content": prompt})

                response = self._client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                latency = time.time() - start_time
                raw_text = response.choices[0].message.content or "{}"
                data = json.loads(raw_text)
                in_tokens = response.usage.prompt_tokens if response.usage else len(prompt.split())
                out_tokens = response.usage.completion_tokens if response.usage else len(raw_text.split())

                return LLMResponse(
                    text=raw_text,
                    structured_data=data,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    latency_seconds=round(latency, 2),
                    model=target_model,
                    provider="openai",
                )
            except Exception as e:
                logger.error(f"OpenAI generate_structured failed: {e}")

        # Fallback simulation
        latency = time.time() - start_time
        return LLMResponse(
            text="{}",
            structured_data={},
            input_tokens=len(prompt.split()),
            output_tokens=10,
            latency_seconds=round(latency, 2),
            model=target_model,
            provider="openai",
        )
