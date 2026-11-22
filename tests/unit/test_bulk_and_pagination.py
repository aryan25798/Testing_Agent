"""
Unit Tests for Server-Side Pagination and Bulk Operations.
Validates pagination structures, search/filter parameters, bulk deletion cascades,
bulk approvals, and active workflow safety checks.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.workflow_runner import workflow_runner, WorkflowRecord, WorkflowState

client = TestClient(app)


def test_paginated_projects_listing():
    # Create 3 distinct projects
    p_ids = []
    for i in range(1, 4):
        res = client.post(
            "/api/v1/projects",
            json={
                "name": f"Paging Test Project {i}",
                "description": f"Pagination test description {i}",
                "framework": "playwright" if i % 2 == 1 else "selenium",
                "base_url": f"http://app-{i}.example.com",
            },
        )
        assert res.status_code == 201
        p_ids.append(res.json()["id"])

    try:
        # Request page 1 with page_size=2
        res = client.get("/api/v1/projects?page=1&page_size=2")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] >= 3

        # Request page 2 with page_size=2
        res2 = client.get("/api/v1/projects?page=2&page_size=2")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["page"] == 2
        assert len(data2["items"]) >= 1

        # Search test
        search_res = client.get("/api/v1/projects?page=1&page_size=10&search=Paging Test Project 2")
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["total"] == 1
        assert search_data["items"][0]["name"] == "Paging Test Project 2"

        # Framework filter test
        fw_res = client.get("/api/v1/projects?page=1&page_size=10&framework=selenium&search=Paging Test")
        assert fw_res.status_code == 200
        fw_data = fw_res.json()
        for item in fw_data["items"]:
            assert item["framework"] == "selenium"

    finally:
        # Cleanup
        client.post("/api/v1/projects/bulk-delete", json={"ids": p_ids})


def test_projects_bulk_delete_and_cascade():
    # Create 2 projects
    res1 = client.post(
        "/api/v1/projects",
        json={"name": "Bulk Del Alpha", "framework": "playwright", "base_url": "http://alpha.com"},
    )
    p1_id = res1.json()["id"]

    res2 = client.post(
        "/api/v1/projects",
        json={"name": "Bulk Del Beta", "framework": "selenium", "base_url": "http://beta.com"},
    )
    p2_id = res2.json()["id"]

    # Create Requirement & Scenario for p1 to satisfy FK
    req = client.post(
        "/api/v1/requirements",
        json={
            "project_id": p1_id,
            "requirement_key": "REQ-BULK-01",
            "title": "Requirement Alpha",
            "description": "For cascade testing",
        },
    ).json()

    scen = client.post(
        "/api/v1/scenarios",
        json={
            "project_id": p1_id,
            "requirement_id": req["id"],
            "scenario_key": "SCEN-BULK-01",
            "title": "Scenario Alpha",
            "description": "Scenario for cascade testing",
            "expected_outcome": "Outcome",
        },
    ).json()

    # Add a test case to p1
    tc_res = client.post(
        "/api/v1/test-cases",
        json={
            "project_id": p1_id,
            "scenario_id": scen["id"],
            "requirement_id": req["id"],
            "test_case_key": "TC-BULK-01",
            "title": "Child Test Case",
            "objective": "Verify cascade delete",
            "expected_results": "Should be deleted",
        },
    )
    assert tc_res.status_code == 201
    tc_id = tc_res.json()["id"]

    # Execute bulk delete
    bulk_res = client.post("/api/v1/projects/bulk-delete", json={"ids": [p1_id, p2_id]})
    assert bulk_res.status_code == 200
    bulk_data = bulk_res.json()
    assert bulk_data["deleted_count"] == 2
    assert p1_id in bulk_data["deleted_ids"]
    assert p2_id in bulk_data["deleted_ids"]

    # Verify projects no longer exist
    assert client.get(f"/api/v1/projects/{p1_id}").status_code == 404
    assert client.get(f"/api/v1/projects/{p2_id}").status_code == 404

    # Verify child test case was cascaded
    tc_check = client.get(f"/api/v1/test-cases/project/{p1_id}")
    assert tc_check.status_code == 200
    assert len(tc_check.json()) == 0



def test_project_delete_active_workflow_conflict():
    # Create project
    res = client.post(
        "/api/v1/projects",
        json={"name": "Active Workflow Guard Project", "framework": "playwright"},
    )
    proj_id = res.json()["id"]

    # Register an active workflow in workflow_runner
    rec = WorkflowRecord(
        workflow_id="wf-test-active-guard",
        project_id=proj_id,
        state=WorkflowState.RUNNING,
    )
    with workflow_runner._lock:
        workflow_runner._workflows[rec.workflow_id] = rec

    try:
        # Attempt individual delete -> should be blocked with 409
        del_res = client.delete(f"/api/v1/projects/{proj_id}")
        assert del_res.status_code == 409
        assert "automated testing workflow is actively running" in del_res.json()["detail"]

        # Attempt bulk delete -> should register as failed_ids
        bulk_res = client.post("/api/v1/projects/bulk-delete", json={"ids": [proj_id]})
        assert bulk_res.status_code == 200
        assert bulk_res.json()["deleted_count"] == 0
        assert proj_id in bulk_res.json()["failed_ids"]

    finally:
        # Clean up workflow record
        with workflow_runner._lock:
            workflow_runner._workflows.pop("wf-test-active-guard", None)
        # Clean up project
        client.delete(f"/api/v1/projects/{proj_id}")


def test_test_cases_pagination_and_bulk_operations():
    # Setup project
    p_res = client.post(
        "/api/v1/projects",
        json={"name": "TC Ops Project", "framework": "playwright"},
    )
    proj_id = p_res.json()["id"]

    tc_ids = []
    try:
        # Create Requirement & Scenario to satisfy FK
        req = client.post(
            "/api/v1/requirements",
            json={
                "project_id": proj_id,
                "requirement_key": "REQ-TC-01",
                "title": "Requirement for TC Ops",
                "description": "Description",
            },
        ).json()

        scen = client.post(
            "/api/v1/scenarios",
            json={
                "project_id": proj_id,
                "requirement_id": req["id"],
                "scenario_key": "SCEN-TC-01",
                "title": "Scenario for TC Ops",
                "description": "Description",
                "expected_outcome": "Expected Outcome",
            },
        ).json()

        # Create 3 test cases
        for i in range(1, 4):
            tc = client.post(
                "/api/v1/test-cases",
                json={
                    "project_id": proj_id,
                    "scenario_id": scen["id"],
                    "requirement_id": req["id"],
                    "test_case_key": f"TC-PAGED-0{i}",
                    "title": f"Test Case Title {i}",
                    "objective": f"Objective {i}",
                    "expected_results": f"Outcome {i}",
                    "is_approved": False,
                },
            ).json()
            tc_ids.append(tc["id"])


        # Test paginated retrieval
        paged_res = client.get(f"/api/v1/test-cases/project/{proj_id}?page=1&page_size=2")
        assert paged_res.status_code == 200
        paged_data = paged_res.json()
        assert paged_data["total"] == 3
        assert len(paged_data["items"]) == 2
        assert paged_data["total_pages"] == 2

        # Test bulk approve
        approve_res = client.post(
            "/api/v1/test-cases/bulk-approve",
            json={"ids": [tc_ids[0], tc_ids[1]]},
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["approved_count"] == 2

        # Verify approval state
        check_res = client.get(f"/api/v1/test-cases/project/{proj_id}")
        cases_by_id = {c["id"]: c for c in check_res.json()}
        assert cases_by_id[tc_ids[0]]["is_approved"] is True
        assert cases_by_id[tc_ids[1]]["is_approved"] is True
        assert cases_by_id[tc_ids[2]]["is_approved"] is False

        # Test bulk delete
        bulk_del_res = client.post(
            "/api/v1/test-cases/bulk-delete",
            json={"ids": [tc_ids[0], tc_ids[1]]},
        )
        assert bulk_del_res.status_code == 200
        assert bulk_del_res.json()["deleted_count"] == 2

        # Verify only 1 remaining
        remaining_res = client.get(f"/api/v1/test-cases/project/{proj_id}")
        assert len(remaining_res.json()) == 1
        assert remaining_res.json()[0]["id"] == tc_ids[2]

    finally:
        client.delete(f"/api/v1/projects/{proj_id}")


def test_executions_pagination_and_bulk_delete():
    # Setup project
    p_res = client.post(
        "/api/v1/projects",
        json={"name": "Exec Ops Project", "framework": "playwright"},
    )
    proj_id = p_res.json()["id"]

    exec_ids = []
    try:
        # Create 3 execution records directly via DB session
        from src.database.session import SessionLocal
        from src.models.entities import TestExecution
        import uuid

        db = SessionLocal()
        try:
            for i in range(1, 4):
                ex = TestExecution(
                    project_id=proj_id,
                    execution_key=f"RUN-PAGED-0{i}",
                    runner_type="playwright",
                    browser="chromium",
                    target_environment="QA",
                    total_tests=5,
                    passed_tests=4,
                    failed_tests=1,
                    execution_duration_seconds=12.5,
                )
                db.add(ex)
                db.commit()
                db.refresh(ex)
                exec_ids.append(ex.id)
        finally:
            db.close()

        # Test pagination
        res = client.get(f"/api/v1/executions/project/{proj_id}?page=1&page_size=2")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["total_pages"] == 2

        # Test bulk delete executions
        del_res = client.post(
            "/api/v1/executions/bulk-delete",
            json={"ids": [exec_ids[0], exec_ids[1]]},
        )
        assert del_res.status_code == 200
        assert del_res.json()["deleted_count"] == 2

        # Verify only 1 execution remains
        rem_res = client.get(f"/api/v1/executions/project/{proj_id}")
        assert len(rem_res.json()) == 1
        assert rem_res.json()[0]["id"] == exec_ids[2]

    finally:
        client.delete(f"/api/v1/projects/{proj_id}")
