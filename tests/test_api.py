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


def test_update_task_title(client):
    client.post("/tasks", json={"id": 1, "title": "Original", "status": "todo"})
    response = client.patch(f"/tasks/{1}", json={"title": "Updated"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_update_task_status(client):
    client.post("/tasks", json={"id": 1, "title": "Original", "status": "todo"})
    response = client.patch(f"/tasks/{1}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_task(client):
    client.post("/tasks", json={"id": 1, "title": "Delete me", "status": "todo"})
    response = client.delete(f"/tasks/{1}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{1}").status_code == 404


def test_filter_tasks_by_status(client):
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "in_progress"})
    response = client.get("/tasks?status=todo")
    assert len(response.json()) == 1


def test_count_tasks(client):
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    response = client.get("/tasks/count")
    assert response.json() == {"count": 1}
