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


def test_patch_task_title(client):
    client.post("/tasks", json={"id": 1, "title": "Test"})
    res = client.patch("/tasks/1", json={"title": "Updated"})
    assert res.status_code == 200
    assert res.json()["title"] == "Updated"


def test_patch_task_status(client):
    client.post("/tasks", json={"id": 1, "title": "Test", "status": "todo"})
    res = client.patch("/tasks/1", json={"status": "done"})
    assert res.json()["status"] == "done"


def test_patch_missing_task(client):
    res = client.patch("/tasks/999", json={"title": "Nope"})
    assert res.status_code == 404


def test_delete_task(client):
    client.post("/tasks", json={"id": 1, "title": "Test"})
    res = client.delete("/tasks/1")
    assert res.status_code == 204
    assert client.get("/tasks/1").status_code == 404


def test_delete_missing_task(client):
    res = client.delete("/tasks/999")
    assert res.status_code == 404


def test_filter_tasks_by_status(client):
    client.post("/tasks", json={"id": 1, "title": "Test1", "status": "todo"})
    client.post("/tasks", json={"id": 2, "title": "Test2", "status": "done"})
    res = client.get("/tasks?status=done")
    assert len(res.json()) == 1


def test_task_count_endpoint(client):
    client.post("/tasks", json={"id": 1, "title": "Test", "status": "todo"})
    res = client.get("/tasks/count?status=todo")
    assert res.json() == {"count": 1}
