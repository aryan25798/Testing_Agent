"""
Unit Tests for Universal Dynamic AI Model Engine & Agent Routing.
"""

import pytest
from src.llm.registry.model_registry import model_registry
from src.llm.router.agent_model_router import agent_model_router


def test_model_registry_discovery():
    models = model_registry.get_models()
    assert len(models) > 0
    providers = {m.provider for m in models}
    assert "gemini" in providers
    assert "openai" in providers


def test_agent_model_router_defaults():
    configs = agent_model_router.get_all_configurations()
    assert len(configs) == 6
    assert "agent_1_requirement_analysis" in configs
    assert "agent_4_test_automation" in configs


def test_runtime_model_switching():
    # Switch agent 1 from gemini to openai
    updated = agent_model_router.set_agent_model(
        agent_id="agent_1_requirement_analysis",
        provider="openai",
        model_id="gpt-4o",
    )
    assert updated["provider"] == "openai"
    assert updated["model_id"] == "gpt-4o"

    # Switch back to gemini
    restored = agent_model_router.set_agent_model(
        agent_id="agent_1_requirement_analysis",
        provider="gemini",
        model_id="gemini-2.5-flash",
    )
    assert restored["provider"] == "gemini"
    assert restored["model_id"] == "gemini-2.5-flash"


def test_invalid_provider_rejected():
    with pytest.raises(ValueError):
        agent_model_router.set_agent_model(
            agent_id="agent_1_requirement_analysis",
            provider="unsupported_provider",
            model_id="fake-model",
        )
