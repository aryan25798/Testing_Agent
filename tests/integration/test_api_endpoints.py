"""
Integration Tests for FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data


def test_project_crud():
    # Create Project
    payload = {
        "name": "Integration Test Project",
        "description": "Created during integration testing",
        "framework": "playwright",
        "base_url": "http://127.0.0.1:8000",
    }
    create_res = client.post("/api/v1/projects", json=payload)
    assert create_res.status_code == 201
    created_proj = create_res.json()
    project_id = created_proj["id"]
    assert created_proj["name"] == "Integration Test Project"

    # Get Project
    get_res = client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200

    # Project Dashboard
    dash_res = client.get(f"/api/v1/projects/{project_id}/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "metrics" in dash_data
    assert "test_results_overview" in dash_data

    # Clean up (Delete)
    del_res = client.delete(f"/api/v1/projects/{project_id}")
    assert del_res.status_code == 204


def test_models_endpoint():
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0


def test_agent_configuration_endpoint():
    res = client.get("/api/v1/agents/configuration")
    assert res.status_code == 200
    data = res.json()
    assert "agent_1_requirement_analysis" in data
