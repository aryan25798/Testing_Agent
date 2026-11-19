"""
Model Capabilities and Metadata Definitions.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ModelCapability(BaseModel):
    model_id: str
    provider: str
    display_name: str
    context_window: int = 128000
    supports_tools: bool = True
    supports_structured_output: bool = True
    supports_vision: bool = False
    is_available: bool = True
    cost_per_million_input_tokens: float = 0.0
    cost_per_million_output_tokens: float = 0.0


KNOWN_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # Google Gemini Models
    "gemini-2.5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "context_window": 1000000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
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
        "cost_in": 0.15,
        "cost_out": 0.60,
    },
    "o1": {
        "display_name": "o1 Reasoning",
        "provider": "openai",
        "context_window": 200000,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
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
        "cost_in": 1.10,
        "cost_out": 4.40,
    },
}
