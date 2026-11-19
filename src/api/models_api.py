"""
AI Models and Agent Model Configuration API Endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.llm.registry.model_registry import model_registry
from src.llm.router.agent_model_router import agent_model_router
from src.schemas.dtos import ModelInfo

router = APIRouter(tags=["AI Models & Agent Routing"])


class SwitchModelRequest(BaseModel):
    provider: str
    model_id: str


@router.get("/models", response_model=List[ModelInfo])
def list_models():
    """Lists all dynamically discovered AI models across Gemini and OpenAI."""
    return model_registry.get_models()


@router.get("/models/available", response_model=List[ModelInfo])
def list_available_models():
    """Lists active models currently verified as available."""
    models = model_registry.get_models()
    return [m for m in models if m.is_available]


@router.post("/models/refresh", response_model=List[ModelInfo])
def refresh_models():
    """Forces dynamic refresh of model lists from provider APIs."""
    return model_registry.refresh_models()


@router.post("/models/test", response_model=Dict[str, bool])
def test_provider_connections():
    """Tests live connectivity to Gemini and OpenAI APIs."""
    return model_registry.test_providers()


@router.get("/agents/configuration")
def get_agents_configuration():
    """Returns the current model assignment for each of the 6 specialized testing agents."""
    return agent_model_router.get_all_configurations()


@router.post("/agents/{agent_id}/switch-model")
def switch_agent_model(agent_id: str, payload: SwitchModelRequest):
    """Dynamically switches the provider and model for a specific agent without restarting."""
    try:
        updated = agent_model_router.set_agent_model(
            agent_id=agent_id,
            provider=payload.provider,
            model_id=payload.model_id,
        )
        return {
            "status": "success",
            "agent_id": agent_id,
            "configuration": updated,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
