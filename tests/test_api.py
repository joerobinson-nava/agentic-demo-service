"""API tests covering current (baseline) behavior.

These tests are all green on the baseline. They intentionally do not cover the
`status` filter (AGENTDEV-1) or the duplicate-id case (AGENTDEV-2); those are
added by the agentic platform as part of the demo.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def _clear_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_tasks_empty(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_task(client):
    payload = {"id": 1, "title": "Write demo", "status": "todo"}
    resp = client.post("/tasks", json=payload)
    assert resp.status_code == 201
    assert resp.json() == payload

    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == [payload]


def test_create_task_defaults_status_to_todo(client):
    resp = client.post("/tasks", json={"id": 2, "title": "No status"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "todo"


def test_get_task(client):
    client.post("/tasks", json={"id": 3, "title": "Fetch me", "status": "done"})
    resp = client.get("/tasks/3")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Fetch me"


def test_get_missing_task_returns_404(client):
    resp = client.get("/tasks/999")
    assert resp.status_code == 404


def test_list_tasks_filtered_by_status(client):
    """GET /tasks?status=X returns only tasks with that status."""
    client.post("/tasks", json={"id": 1, "title": "Todo task", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "In progress task", "status": "in_progress"})
    client.post("/tasks", json={"id": 3, "title": "Done task", "status": "done"})

    resp = client.get("/tasks?status=todo")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == 1

    resp = client.get("/tasks?status=in_progress")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == 2

    resp = client.get("/tasks?status=done")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == 3


def test_count_tasks_all(client):
    """GET /tasks/count returns total count when no status filter provided."""
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "in_progress"})

    resp = client.get("/tasks/count")
    assert resp.status_code == 200
    assert resp.json() == {"count": 2}


def test_count_tasks_by_status(client):
    """GET /tasks/count?status=X returns count of tasks with that status."""
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "todo"})
    client.post("/tasks", json={"id": 3, "title": "Task 3", "status": "done"})

    resp = client.get("/tasks/count?status=todo")
    assert resp.status_code == 200
    assert resp.json() == {"count": 2}

    resp = client.get("/tasks/count?status=done")
    assert resp.status_code == 200
    assert resp.json() == {"count": 1}


def test_update_task_title_only(client):
    """PATCH /tasks/{id} updates only the title when status not provided."""
    create_resp = client.post(
        "/tasks", json={"id": 1, "title": "Original", "status": "todo"}
    )
    assert create_resp.status_code == 201

    update_resp = client.patch("/tasks/1", json={"title": "Updated"})
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == 1
    assert data["title"] == "Updated"
    assert data["status"] == "todo"


def test_update_task_status_only(client):
    """PATCH /tasks/{id} updates only the status when title not provided."""
    client.post("/tasks", json={"id": 1, "title": "Task", "status": "todo"})

    update_resp = client.patch("/tasks/1", json={"status": "in_progress"})
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == 1
    assert data["title"] == "Task"
    assert data["status"] == "in_progress"


def test_update_task_both_fields(client):
    """PATCH /tasks/{id} updates both title and status when both provided."""
    client.post("/tasks", json={"id": 1, "title": "Original", "status": "todo"})

    update_resp = client.patch("/tasks/1", json={"title": "Updated", "status": "done"})
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == 1
    assert data["title"] == "Updated"
    assert data["status"] == "done"


def test_update_task_not_found(client):
    """PATCH /tasks/{id} returns 404 for non-existent task."""
    resp = client.patch("/tasks/999", json={"title": "Nope"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_delete_task_success(client):
    """DELETE /tasks/{id} returns 204 and task is no longer retrievable."""
    client.post("/tasks", json={"id": 1, "title": "ToDelete", "status": "todo"})

    delete_resp = client.delete("/tasks/1")
    assert delete_resp.status_code == 204

    get_resp = client.get("/tasks/1")
    assert get_resp.status_code == 404


def test_delete_task_not_found(client):
    """DELETE /tasks/{id} returns 404 for non-existent task."""
    resp = client.delete("/tasks/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"
