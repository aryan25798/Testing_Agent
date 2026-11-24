"""
Model Capabilities and Metadata Definitions.
"""

import re
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field


class ModelCapability(BaseModel):
    model_id: str
    provider: str
    display_name: str
    context_window: int = 128000
    supports_tools: bool = True
    supports_structured_output: bool = True
    supports_vision: bool = False
    supports_custom_temperature: bool = True
    supports_system_role: bool = True
    uses_max_completion_tokens: bool = False
    is_available: bool = True
    cost_per_million_input_tokens: float = 0.0
    cost_per_million_output_tokens: float = 0.0


# Dynamically learned model capabilities across sessions and runtime discovery
MODELS_WITHOUT_CUSTOM_TEMPERATURE: Set[str] = {
    "o1", "o1-preview", "o1-mini", "o3-mini", "o3", "gpt-6.2-sol", "gpt-6.1-sol", "gpt-6-sol",
    "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro", "gpt-5.1", "gpt-5.2", "gpt-5.4", "gpt-5.5",
    "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6-sol", "gpt-6-astra", "gpt-6.1-terra", "gpt-6.2-astra"
}

MODELS_REQUIRING_MAX_COMPLETION_TOKENS: Set[str] = {
    "o1", "o1-preview", "o1-mini", "o3-mini", "o3", "gpt-6.2-sol", "gpt-6.1-sol", "gpt-6-sol",
    "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro", "gpt-5.1", "gpt-5.2", "gpt-5.4", "gpt-5.5",
    "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6-sol", "gpt-6-astra", "gpt-6.1-terra", "gpt-6.2-astra"
}

MODELS_REQUIRING_DEVELOPER_ROLE: Set[str] = {
    "o1", "o1-preview", "o1-mini", "o3-mini", "o3"
}


def is_custom_temperature_supported(model_id: str) -> bool:
    """Checks whether an OpenAI or compatible model supports custom temperature (e.g. 0.1, 0.2)."""
    mid = (model_id or "").lower().strip()
    if mid in MODELS_WITHOUT_CUSTOM_TEMPERATURE:
        return False
    # Regex heuristics for reasoning, o-series, and advanced sol/terra/luna/astra architectures
    if re.search(r"^(o1|o3|gpt-5|gpt-6|.*-sol\b|.*-luna\b|.*-terra\b|.*-astra\b|.*reasoning)", mid, re.IGNORECASE):
        return False
    return True


def mark_model_temperature_unsupported(model_id: str):
    """Dynamically marks a model as not supporting custom temperature after an HTTP 400 rejection."""
    if model_id:
        MODELS_WITHOUT_CUSTOM_TEMPERATURE.add(model_id.lower().strip())


def uses_max_completion_tokens(model_id: str) -> bool:
    """Checks whether an OpenAI model requires 'max_completion_tokens' instead of 'max_tokens'."""
    mid = (model_id or "").lower().strip()
    if mid in MODELS_REQUIRING_MAX_COMPLETION_TOKENS:
        return True
    if re.search(r"^(o1|o3|gpt-5|gpt-6|.*-sol\b|.*-luna\b|.*-terra\b|.*-astra\b|.*reasoning)", mid, re.IGNORECASE):
        return True
    return False


def mark_model_requires_max_completion_tokens(model_id: str):
    """Dynamically marks a model as requiring max_completion_tokens after an HTTP 400 rejection."""
    if model_id:
        MODELS_REQUIRING_MAX_COMPLETION_TOKENS.add(model_id.lower().strip())


def prefers_developer_role(model_id: str) -> bool:
    """Checks whether a model requires or prefers 'developer' role instead of 'system'."""
    mid = (model_id or "").lower().strip()
    if mid in MODELS_REQUIRING_DEVELOPER_ROLE:
        return True
    if re.search(r"^(o1|o3|.*reasoning)", mid, re.IGNORECASE):
        return True
    return False


def mark_model_prefers_developer_role(model_id: str):
    """Dynamically marks a model as requiring developer role."""
    if model_id:
        MODELS_REQUIRING_DEVELOPER_ROLE.add(model_id.lower().strip())


KNOWN_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # Google Gemini Models
    "gemini-2.5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "context_window": 1000000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 1.25,
        "cost_out": 5.00,
    },
    "gemini-2.5-flash": {
        "display_name": "Gemini 2.5 Flash",
        "provider": "gemini",
        "context_window": 1000000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 0.075,
        "cost_out": 0.30,
    },
    "gemini-1.5-pro": {
        "display_name": "Gemini 1.5 Pro",
        "provider": "gemini",
        "context_window": 1000000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 1.25,
        "cost_out": 5.00,
    },
    "gemini-1.5-flash": {
        "display_name": "Gemini 1.5 Flash",
        "provider": "gemini",
        "context_window": 1000000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 0.075,
        "cost_out": 0.30,
    },
    # OpenAI Models
    "gpt-4o": {
        "display_name": "GPT-4o",
        "provider": "openai",
        "context_window": 128000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 2.50,
        "cost_out": 10.00,
    },
    "gpt-4o-mini": {
        "display_name": "GPT-4o Mini",
        "provider": "openai",
        "context_window": 128000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": True,
        "cost_in": 0.15,
        "cost_out": 0.60,
    },
    "gpt-6.2-sol": {
        "display_name": "GPT-6.2 SOL",
        "provider": "openai",
        "context_window": 200000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": False,
        "cost_in": 3.00,
        "cost_out": 12.00,
    },
    "o1": {
        "display_name": "o1 Reasoning",
        "provider": "openai",
        "context_window": 200000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_custom_temperature": False,
        "cost_in": 15.00,
        "cost_out": 60.00,
    },
    "o3-mini": {
        "display_name": "o3 Mini",
        "provider": "openai",
        "context_window": 200000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": False,
        "supports_custom_temperature": False,
        "cost_in": 1.10,
        "cost_out": 4.40,
    },
}
