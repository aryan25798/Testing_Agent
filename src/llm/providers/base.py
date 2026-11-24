"""
Base Interface for LLM Providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel


class LLMResponse(BaseModel):
    text: str
    structured_data: Optional[Dict[str, Any]] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    model: str
    provider: str


class BaseLLMProvider(ABC):
    """Abstract interface that all LLM provider adapters must implement."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    def test_connection(self) -> bool:
        """Validates that credentials are valid and the provider endpoint is reachable."""
        pass

    @abstractmethod
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Dynamically retrieves the list of accessible models from the provider."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generates raw text response."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Generates a structured Pydantic object or JSON dictionary response."""
        pass
