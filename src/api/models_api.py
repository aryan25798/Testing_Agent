"""
AI Models and Agent Model Configuration API Endpoints.
Secured with AES-256-GCM encrypted local vault, masked credentials responses,
and tamper-evident audit logging.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from src.llm.registry.model_registry import model_registry
from src.llm.router.agent_model_router import agent_model_router
from src.schemas.dtos import ModelInfo
from src.core.security.secrets_manager import secrets_manager
from src.core.security.audit_logger import audit_logger
from src.core.security.sanitizer import prompt_sanitizer
from src.config.settings import settings

router = APIRouter(tags=["AI Models & Agent Routing"])


class SwitchModelRequest(BaseModel):
    provider: str = Field(..., pattern="^(gemini|openai)$")
    model_id: str = Field(..., min_length=2, max_length=100)


class SetCredentialsRequest(BaseModel):
    provider: str = Field(..., pattern="^(gemini|openai)$")
    api_key: str = Field(..., min_length=8, max_length=256)


class CredentialStatusResponse(BaseModel):
    provider: str
    is_configured: bool
    masked: Optional[str] = None


@router.post("/models/credentials")
def set_provider_credentials(payload: SetCredentialsRequest):
    """
    Sets credentials for Gemini or OpenAI.
    Validates with provider API, securely encrypts at rest using AES-256-GCM,
    and updates in-memory provider clients without writing plaintext to .env.
    """
    provider_name = payload.provider.lower().strip()
    clean_key = payload.api_key.strip()

    try:
        # Update provider credentials in memory
        if provider_name == "gemini":
            model_registry.gemini_provider.set_api_key(clean_key)
        elif provider_name == "openai":
            model_registry.openai_provider.set_api_key(clean_key)
        else:
            raise HTTPException(status_code=400, detail="Unsupported model provider.")

        # Test connectivity
        test_results = model_registry.test_providers()
        is_valid = test_results.get(provider_name, False)

        # Securely store in encrypted vault
        secrets_manager.store_secret(provider_name, clean_key)

        # Audit log the credential storage event
        audit_logger.log_event(
            action="STORE_CREDENTIALS",
            status="SUCCESS" if is_valid else "WARNING",
            details={
                "provider": provider_name,
                "is_valid": is_valid,
                "masked": secrets_manager.mask_secret(clean_key),
            },
        )

        if is_valid:
            model_registry.refresh_models()

        return {
            "status": "success",
            "provider": provider_name,
            "is_valid": is_valid,
            "masked": secrets_manager.mask_secret(clean_key),
            "available_models_count": len([m for m in model_registry.get_models() if m.is_available]),
        }
    except Exception as e:
        safe_msg = prompt_sanitizer.redact_secrets(str(e))
        audit_logger.log_event(
            action="STORE_CREDENTIALS",
            status="FAILED",
            details={"provider": provider_name, "error": safe_msg},
            severity="HIGH",
        )
        raise HTTPException(status_code=400, detail=safe_msg)


@router.get("/models/credentials/status", response_model=Dict[str, CredentialStatusResponse])
def get_credentials_status():
    """
    Returns masked configuration status for all providers.
    Never exposes raw API keys to browser, logs, or API responses.
    """
    return {
        "gemini": CredentialStatusResponse(
            provider="gemini",
            is_configured=secrets_manager.is_configured("gemini"),
            masked=secrets_manager.get_status("gemini").get("masked"),
        ),
        "openai": CredentialStatusResponse(
            provider="openai",
            is_configured=secrets_manager.is_configured("openai"),
            masked=secrets_manager.get_status("openai").get("masked"),
        ),
    }


@router.get("/models/first-run-status")
def get_first_run_status():
    """
    Checks whether the platform has at least one configured AI provider and browser environment ready.
    Used by the frontend first-run onboarding wizard.
    """
    gemini_ready = secrets_manager.is_configured("gemini")
    openai_ready = secrets_manager.is_configured("openai")

    browser_ready = True
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
            browser_ready = bool(path and Path(path).exists())
    except Exception:
        browser_ready = False

    return {
        "needs_setup": not (gemini_ready or openai_ready),
        "gemini_configured": gemini_ready,
        "openai_configured": openai_ready,
        "browser_ready": browser_ready,
        "default_provider": settings.DEFAULT_PROVIDER,
    }


@router.delete("/models/credentials/{provider}")
def delete_provider_credentials(provider: str):
    """
    Deletes provider credential from encrypted vault and memory.
    """
    prov_lower = provider.lower().strip()
    if prov_lower not in ["gemini", "openai"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Must be 'gemini' or 'openai'.")

    deleted = secrets_manager.delete_secret(prov_lower)
    model_registry.clear_credentials(prov_lower)

    audit_logger.log_event(
        action="REVOKE_CREDENTIALS",
        status="SUCCESS" if deleted else "NOT_FOUND",
        details={"provider": prov_lower},
    )

    return {
        "status": "success",
        "provider": prov_lower,
        "deleted": deleted,
    }


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
        audit_logger.log_event(
            action="SWITCH_AGENT_MODEL",
            status="SUCCESS",
            details={"agent_id": agent_id, "provider": payload.provider, "model_id": payload.model_id},
        )
        return {
            "status": "success",
            "agent_id": agent_id,
            "configuration": updated,
        }
    except Exception as e:
        safe_msg = prompt_sanitizer.redact_secrets(str(e))
        raise HTTPException(status_code=400, detail=safe_msg)
