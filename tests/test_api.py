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


def test_list_tasks_pagination_default(client):
    # Create 15 tasks
    for i in range(1, 16):
        client.post("/tasks", json={"id": i, "title": f"Task {i}", "status": "todo"})
    
    # Default limit is 10
    resp = client.get("/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 10
    assert tasks[0]["id"] == 1
    assert tasks[9]["id"] == 10


def test_list_tasks_pagination_with_limit(client):
    # Create 10 tasks
    for i in range(1, 11):
        client.post("/tasks", json={"id": i, "title": f"Task {i}", "status": "todo"})
    
    # Request 5 tasks
    resp = client.get("/tasks?limit=5")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 5
    assert tasks[0]["id"] == 1
    assert tasks[4]["id"] == 5


def test_list_tasks_pagination_with_offset(client):
    # Create 10 tasks
    for i in range(1, 11):
        client.post("/tasks", json={"id": i, "title": f"Task {i}", "status": "todo"})
    
    # Skip first 5 tasks
    resp = client.get("/tasks?offset=5")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 5
    assert tasks[0]["id"] == 6
    assert tasks[4]["id"] == 10


def test_list_tasks_pagination_with_limit_and_offset(client):
    # Create 15 tasks
    for i in range(1, 16):
        client.post("/tasks", json={"id": i, "title": f"Task {i}", "status": "todo"})
    
    # Get tasks 6-10 (offset=5, limit=5)
    resp = client.get("/tasks?limit=5&offset=5")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 5
    assert tasks[0]["id"] == 6
    assert tasks[4]["id"] == 10


def test_list_tasks_pagination_offset_beyond_end(client):
    # Create 5 tasks
    for i in range(1, 6):
        client.post("/tasks", json={"id": i, "title": f"Task {i}", "status": "todo"})
    
    # Request offset beyond available tasks
    resp = client.get("/tasks?offset=10")
    assert resp.status_code == 200
    assert resp.json() == []
