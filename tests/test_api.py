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


def test_update_task(client):
    client.post("/tasks", json={"id": 1, "title": "Original", "status": "todo"})
    resp = client.put("/tasks/1", json={"id": 1, "title": "Updated", "status": "done"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    assert resp.json()["status"] == "done"


def test_update_missing_task_returns_404(client):
    resp = client.put("/tasks/999", json={"id": 999, "title": "Missing", "status": "todo"})
    assert resp.status_code == 404


def test_delete_task(client):
    client.post("/tasks", json={"id": 1, "title": "Delete me", "status": "todo"})
    resp = client.delete("/tasks/1")
    assert resp.status_code == 204

    resp = client.get("/tasks/1")
    assert resp.status_code == 404


def test_delete_missing_task_returns_404(client):
    resp = client.delete("/tasks/999")
    assert resp.status_code == 404


def test_filter_tasks_by_status(client):
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "in_progress"})
    client.post("/tasks", json={"id": 3, "title": "Task 3", "status": "done"})
    client.post("/tasks", json={"id": 4, "title": "Task 4", "status": "todo"})

    resp = client.get("/tasks?status=todo")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 2
    assert all(t["status"] == "todo" for t in tasks)

    resp = client.get("/tasks?status=in_progress")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2

    resp = client.get("/tasks?status=done")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filter_by_invalid_status_returns_empty(client):
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    resp = client.get("/tasks?status=invalid")
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_with_no_status_returns_all(client):
    client.post("/tasks", json={"id": 1, "title": "Task 1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "done"})
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

