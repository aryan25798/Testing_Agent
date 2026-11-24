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
from src.core.exceptions import ProviderUnavailableError, LLMGenerationError

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

    def _build_completion_payload(
        self,
        target_model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        structured_json: bool = False,
    ) -> Dict[str, Any]:
        """Builds capability-aware chat completion parameters for OpenAI models."""
        from src.llm.capabilities.models import (
            is_custom_temperature_supported,
            uses_max_completion_tokens,
            prefers_developer_role,
        )

        use_dev_role = prefers_developer_role(target_model)

        messages = []
        if system_prompt:
            role = "developer" if use_dev_role else "system"
            content = system_prompt
            if structured_json:
                content += "\nYou MUST return valid, well-formed RFC-8259 JSON matching the requested schema."
            messages.append({"role": role, "content": content})
        elif structured_json:
            role = "developer" if use_dev_role else "system"
            messages.append({"role": role, "content": "You MUST return valid, well-formed RFC-8259 JSON."})

        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
        }

        # Temperature: only send if the model actually supports custom temperature and temperature is specified
        if is_custom_temperature_supported(target_model):
            if temperature is not None:
                payload["temperature"] = temperature
        else:
            logger.debug(f"Omitted custom temperature parameter for capability-restricted model '{target_model}'.")

        # Token limits: distinction between max_tokens and max_completion_tokens
        if max_tokens:
            if uses_max_completion_tokens(target_model):
                payload["max_completion_tokens"] = max_tokens
            else:
                payload["max_tokens"] = max_tokens

        # Structured JSON response format
        if structured_json:
            payload["response_format"] = {"type": "json_object"}

        return payload

    def _execute_completion_with_auto_correction(self, payload: Dict[str, Any]) -> Any:
        """
        Executes OpenAI chat completion with automatic parameter error recovery
        for temperature, max_tokens/max_completion_tokens, and system role mismatches.
        Never retries permanent non-parameter errors.
        """
        from src.llm.capabilities.models import (
            mark_model_temperature_unsupported,
            mark_model_requires_max_completion_tokens,
            mark_model_prefers_developer_role,
        )

        current_payload = dict(payload)
        target_model = current_payload.get("model", "")

        for attempt in range(3):
            try:
                return self._client.chat.completions.create(**current_payload)
            except Exception as e:
                err_msg = str(e)
                err_lower = err_msg.lower()

                # 1. Temperature parameter rejection (e.g. 400 Unsupported value: 'temperature')
                if "temperature" in err_lower and any(w in err_lower for w in ["does not support", "only the default", "unsupported value", "invalid parameter"]):
                    logger.warning(f"Model '{target_model}' rejected custom temperature. Auto-correcting payload by stripping temperature.")
                    mark_model_temperature_unsupported(target_model)
                    current_payload.pop("temperature", None)
                    continue

                # 2. max_tokens vs max_completion_tokens rejection
                if "max_tokens" in err_lower and ("max_completion_tokens" in err_lower or "unsupported" in err_lower):
                    logger.warning(f"Model '{target_model}' requires max_completion_tokens. Auto-correcting payload.")
                    mark_model_requires_max_completion_tokens(target_model)
                    val = current_payload.pop("max_tokens", None)
                    if val:
                        current_payload["max_completion_tokens"] = val
                    continue

                # 3. System role rejection
                if "role" in err_lower and "system" in err_lower:
                    logger.warning(f"Model '{target_model}' rejected system role. Converting to developer role.")
                    mark_model_prefers_developer_role(target_model)
                    converted_msgs = []
                    for m in current_payload.get("messages", []):
                        if m.get("role") == "system":
                            converted_msgs.append({"role": "developer", "content": m.get("content", "")})
                        else:
                            converted_msgs.append(m)
                    current_payload["messages"] = converted_msgs
                    continue

                # 4. JSON object response_format rejection
                if "response_format" in err_lower and "json_object" in err_lower:
                    logger.warning(f"Model '{target_model}' rejected json_object response_format. Falling back to prompt-guided JSON.")
                    current_payload.pop("response_format", None)
                    continue

                # Permanent configuration errors or network/quota errors: do not retry in this parameter correction loop
                raise e

        # If loop exhausts, attempt one final call with stripped payload
        return self._client.chat.completions.create(**current_payload)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_OPENAI_MODEL
        start_time = time.time()

        if self._client:
            try:
                payload = self._build_completion_payload(
                    target_model=target_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    structured_json=False,
                )
                response = self._execute_completion_with_auto_correction(payload)
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
                raise LLMGenerationError(
                    f"OpenAI generate_text failed for model '{target_model}': {e}",
                    details={"provider": "openai", "model": target_model},
                ) from e

        raise ProviderUnavailableError(
            "OpenAI provider is not initialized. Check API key configuration.",
            details={"provider": "openai", "model": target_model},
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        target_model = model or settings.DEFAULT_OPENAI_MODEL
        start_time = time.time()

        if self._client:
            try:
                schema_hint = ""
                if output_schema:
                    try:
                        schema_hint = f"\nExpected JSON schema:\n{json.dumps(output_schema.model_json_schema())}"
                    except Exception:
                        pass
                full_prompt = f"{prompt}{schema_hint}" if schema_hint else prompt

                payload = self._build_completion_payload(
                    target_model=target_model,
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=None,
                    structured_json=True,
                )
                response = self._execute_completion_with_auto_correction(payload)
                latency = time.time() - start_time
                raw_text = response.choices[0].message.content or "{}"
                from src.core.utils.json_sanitizer import repair_and_parse_json
                data = repair_and_parse_json(raw_text)
                in_tokens = response.usage.prompt_tokens if response.usage else len(full_prompt.split())
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
                err_str = str(e)
                logger.error(f"OpenAI generate_structured failed: {e}")
                if any(t in err_str.lower() for t in ["429", "insufficient_quota", "quota", "rate limit", "ratelimit"]):
                    import re
                    match = re.search(r"retry in (\d+)", err_str.lower()) or re.search(r"retry after (\d+)", err_str.lower())
                    retry_sec = int(match.group(1)) if match else 60
                    from src.core.exceptions import QuotaExceededError
                    raise QuotaExceededError(
                        message=f"OpenAI API Quota / Rate Limit Exceeded (HTTP 429): {err_str}",
                        provider="openai",
                        retry_after_seconds=retry_sec,
                        details={"provider": "openai", "model": target_model, "raw_error": err_str},
                    ) from e

                raise LLMGenerationError(
                    f"OpenAI generate_structured failed for model '{target_model}': {e}",
                    details={"provider": "openai", "model": target_model},
                ) from e

        raise ProviderUnavailableError(
            "OpenAI provider is not initialized. Check API key configuration.",
            details={"provider": "openai", "model": target_model},
        )
