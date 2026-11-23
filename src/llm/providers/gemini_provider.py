"""
Google Gemini API Provider Adapter.
Supports dynamic model discovery, text generation, and structured outputs.
"""

import time
import json
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
from src.llm.providers.base import BaseLLMProvider, LLMResponse
from src.config.settings import settings
from src.core.logging import get_logger
from src.core.exceptions import ProviderUnavailableError, LLMGenerationError

logger = get_logger("gemini_provider")


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            try:
                from src.core.security.secrets_manager import secrets_manager
                api_key = secrets_manager.get_secret("gemini") or secrets_manager.get_secret("gemini_api_key")
            except Exception:
                pass
        super().__init__(api_key=api_key or settings.GEMINI_API_KEY)
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    def set_api_key(self, api_key: str):
        """Updates API key and re-initializes client dynamically."""
        self.api_key = api_key
        self._init_client()

    def test_connection(self) -> bool:
        if not self.api_key or not self._client:
            return False
        try:
            models = self.list_available_models()
            return len(models) > 0
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

    def list_available_models(self) -> List[Dict[str, Any]]:
        default_gemini_models = [
            {"model_id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash", "context_window": 1000000},
            {"model_id": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro", "context_window": 1000000},
            {"model_id": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "context_window": 1000000},
            {"model_id": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "context_window": 1000000},
        ]
        if not self._client:
            return default_gemini_models

        try:
            discovered = []
            for m in self._client.models.list():
                model_name = m.name.replace("models/", "") if hasattr(m, "name") else str(m)
                actions = getattr(m, "supported_actions", None) or []

                # Filter out pure embedding, aqa, and non-generative models
                if actions and "generateContent" not in actions:
                    continue
                if any(x in model_name.lower() for x in ["embedding", "aqa", "text-embedding"]):
                    continue

                raw_display = getattr(m, "display_name", None)
                display_name = raw_display if raw_display else model_name.replace("-", " ").title()
                discovered.append({
                    "model_id": model_name,
                    "display_name": f"{display_name} ({model_name})",
                    "context_window": getattr(m, "input_token_limit", 1000000) or 1000000,
                })
            return discovered if discovered else default_gemini_models
        except Exception as e:
            logger.warning(f"Could not fetch dynamic models list from Gemini API: {e}. Using catalog.")
            return default_gemini_models

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_GEMINI_MODEL
        start_time = time.time()

        if self._client:
            try:
                contents = prompt
                config = {"temperature": temperature, "max_output_tokens": max_tokens}
                if system_prompt:
                    config["system_instruction"] = system_prompt

                response = self._client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=config,
                )
                latency = time.time() - start_time
                text = response.text or ""
                # Approximate token usage
                in_tokens = int(len(prompt.split()) * 1.3)
                out_tokens = int(len(text.split()) * 1.3)
                return LLMResponse(
                    text=text,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    latency_seconds=round(latency, 2),
                    model=target_model,
                    provider="gemini",
                )
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                raise LLMGenerationError(
                    f"Gemini generate_text failed for model '{target_model}': {e}",
                    details={"provider": "gemini", "model": target_model},
                ) from e

        raise ProviderUnavailableError(
            "Gemini provider is not initialized. Check API key configuration.",
            details={"provider": "gemini", "model": target_model},
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_GEMINI_MODEL
        start_time = time.time()

        schema_instruction = ""
        if output_schema:
            schema_instruction = f"\nYou MUST respond exclusively with a valid JSON object matching this schema:\n{json.dumps(output_schema.model_json_schema())}\nDo not wrap output in markdown code blocks or backticks."

        full_prompt = f"{prompt}\n{schema_instruction}"

        if self._client:
            try:
                config = {"temperature": temperature}
                if system_prompt:
                    config["system_instruction"] = system_prompt
                if output_schema:
                    config["response_mime_type"] = "application/json"

                response = self._client.models.generate_content(
                    model=target_model,
                    contents=full_prompt,
                    config=config,
                )
                raw_text = (response.text or "{}").strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                latency = time.time() - start_time
                from src.core.utils.json_sanitizer import repair_and_parse_json
                data = repair_and_parse_json(raw_text)
                return LLMResponse(
                    text=raw_text,
                    structured_data=data,
                    input_tokens=int(len(full_prompt.split()) * 1.3),
                    output_tokens=int(len(raw_text.split()) * 1.3),
                    latency_seconds=round(latency, 2),
                    model=target_model,
                    provider="gemini",
                )
            except Exception as e:
                err_str = str(e)
                logger.error(f"Gemini structured output failed: {e}")
                if any(t in err_str.lower() for t in ["429", "resourceexhausted", "quota", "rate limit", "ratelimit"]):
                    import re
                    match = re.search(r"retry in (\d+)", err_str.lower()) or re.search(r"retry after (\d+)", err_str.lower())
                    retry_sec = int(match.group(1)) if match else 60
                    from src.core.exceptions import QuotaExceededError
                    raise QuotaExceededError(
                        message=f"Gemini API Quota / Rate Limit Exceeded (HTTP 429): {err_str}",
                        provider="gemini",
                        retry_after_seconds=retry_sec,
                        details={"provider": "gemini", "model": target_model, "raw_error": err_str},
                    ) from e

                raise LLMGenerationError(
                    f"Gemini generate_structured failed for model '{target_model}': {e}",
                    details={"provider": "gemini", "model": target_model},
                ) from e

        raise ProviderUnavailableError(
            "Gemini provider is not initialized. Check API key configuration.",
            details={"provider": "gemini", "model": target_model},
        )
