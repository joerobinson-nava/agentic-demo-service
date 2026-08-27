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


def test_update_task_title_only(client):
    """PATCH updates only the title when status is not provided."""
    client.post("/tasks", json={"id": 1, "title": "Original", "status": "todo"})
    response = client.patch("/tasks/1", json={"title": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["status"] == "todo"


def test_update_task_status_only(client):
    """PATCH updates only the status when title is not provided."""
    client.post("/tasks", json={"id": 1, "title": "Task", "status": "todo"})
    response = client.patch("/tasks/1", json={"status": "done"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Task"
    assert data["status"] == "done"


def test_update_missing_task_returns_404(client):
    """PATCH on non-existent task returns 404."""
    response = client.patch("/tasks/999", json={"title": "New"})
    assert response.status_code == 404


def test_delete_task_returns_204(client):
    """DELETE removes a task and returns 204."""
    client.post("/tasks", json={"id": 1, "title": "Task", "status": "todo"})
    response = client.delete("/tasks/1")
    assert response.status_code == 204


def test_deleted_task_not_retrievable(client):
    """GET on deleted task returns 404."""
    client.post("/tasks", json={"id": 1, "title": "Task", "status": "todo"})
    client.delete("/tasks/1")
    response = client.get("/tasks/1")
    assert response.status_code == 404


def test_delete_missing_task_returns_404(client):
    """DELETE on non-existent task returns 404."""
    response = client.delete("/tasks/999")
    assert response.status_code == 404


def test_list_tasks_filtered_by_status(client):
    """GET /tasks?status filters results."""
    client.post("/tasks", json={"id": 1, "title": "Todo", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Done", "status": "done"})
    client.post("/tasks", json={"id": 3, "title": "Also Todo", "status": "todo"})

    response = client.get("/tasks?status=todo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo"
    assert data[1]["title"] == "Also Todo"


def test_count_tasks_all(client):
    """GET /tasks/count returns total count."""
    client.post("/tasks", json={"id": 1, "title": "Todo", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Done", "status": "done"})

    response = client.get("/tasks/count")
    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_count_tasks_filtered_by_status(client):
    """GET /tasks/count?status filters by status."""
    client.post("/tasks", json={"id": 1, "title": "Todo", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Done", "status": "done"})
    client.post("/tasks", json={"id": 3, "title": "Also Todo", "status": "todo"})

    response = client.get("/tasks/count?status=todo")
    assert response.status_code == 200
    assert response.json() == {"count": 2}
