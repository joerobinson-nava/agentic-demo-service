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
    client.post("/tasks", json={"id": 1, "title": "Original title", "status": "todo"})
    resp = client.patch("/tasks/1", json={"title": "Updated title"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "Updated title", "status": "todo"}

    resp = client.patch("/tasks/1", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "Updated title", "status": "in_progress"}


def test_update_missing_task_returns_404(client):
    resp = client.patch("/tasks/999", json={"title": "No such task"})
    assert resp.status_code == 404


def test_update_task_with_both_fields(client):
    client.post("/tasks", json={"id": 2, "title": "Task 2", "status": "todo"})
    resp = client.patch("/tasks/2", json={"title": "New title", "status": "done"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 2, "title": "New title", "status": "done"}

