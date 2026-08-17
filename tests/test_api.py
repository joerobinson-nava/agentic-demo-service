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


def test_exec_success(client):
    payload = {"command": "echo Hello, World!"}
    resp = client.post("/exec", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"stdout": "Hello, World!\n", "stderr": "", "exit_code": 0}


def test_exec_failure(client):
    payload = {"command": "nonexistent_command"}
    resp = client.post("/exec", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"stdout": "", "stderr": "/bin/sh: 1: nonexistent_command: not found\n", "exit_code": 127}


def test_exec_timeout(client):
    payload = {"command": "sleep 30"}
    resp = client.post("/exec", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"stdout": "", "stderr": "Command timed out", "exit_code": 124}
