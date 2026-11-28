"""API tests covering current (baseline) behavior.

These tests are all green on the baseline. They intentionally do not cover the
`status` filter (AGENTDEV-1) or the duplicate-id case (AGENTDEV-2); those are
added by the agentic platform as part of the demo.
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.main import app
from app.store import store

FROZEN = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)


def _parse(value):
    return datetime.fromisoformat(value)


def _ids(client, created_after):
    resp = client.get("/tasks", params={"created_after": created_after})
    assert resp.status_code == 200
    return [t["id"] for t in resp.json()]


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
    expected = {**payload, "created_at": "2024-01-02T03:04:05Z"}
    with freeze_time(FROZEN):
        resp = client.post("/tasks", json=payload)
    assert resp.status_code == 201
    assert resp.json() == expected

    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == [expected]


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


def test_create_task_records_created_at(client):
    with freeze_time(FROZEN):
        resp = client.post("/tasks", json={"id": 1, "title": "Timed"})
    assert resp.status_code == 201
    created_at = _parse(resp.json()["created_at"])
    assert created_at == FROZEN
    assert created_at.utcoffset() == timedelta(0)

    fetched = client.get("/tasks/1").json()
    assert _parse(fetched["created_at"]) == FROZEN


def test_create_task_ignores_client_created_at(client):
    with freeze_time(FROZEN):
        resp = client.post(
            "/tasks", json={"id": 1, "title": "Spoof", "created_at": "2000-01-01T00:00:00Z"}
        )
    assert resp.status_code == 201
    assert _parse(resp.json()["created_at"]) == FROZEN


def _create_two(client):
    with freeze_time(FROZEN):
        client.post("/tasks", json={"id": 1, "title": "A"})
    with freeze_time(FROZEN + timedelta(seconds=10)):
        client.post("/tasks", json={"id": 2, "title": "B"})


def test_list_tasks_created_after_before_creation(client):
    _create_two(client)
    assert _ids(client, (FROZEN - timedelta(seconds=1)).isoformat()) == [1, 2]


def test_list_tasks_created_after_equal_excluded(client):
    with freeze_time(FROZEN):
        client.post("/tasks", json={"id": 1, "title": "A"})
    assert _ids(client, FROZEN.isoformat()) == []


def test_list_tasks_created_after_later_returns_empty(client):
    _create_two(client)
    assert _ids(client, (FROZEN + timedelta(seconds=11)).isoformat()) == []


def test_list_tasks_created_after_splits_tasks(client):
    _create_two(client)
    assert _ids(client, FROZEN.isoformat()) == [2]


def test_list_tasks_without_filter_returns_all(client):
    _create_two(client)
    resp = client.get("/tasks")
    assert [t["id"] for t in resp.json()] == [1, 2]


def test_list_tasks_created_after_offset_and_naive(client):
    with freeze_time(FROZEN):
        client.post("/tasks", json={"id": 1, "title": "A"})
    plus_two = timezone(timedelta(hours=2))
    earlier = (FROZEN - timedelta(seconds=1)).astimezone(plus_two)
    assert _ids(client, earlier.isoformat()) == [1]
    assert _ids(client, FROZEN.replace(tzinfo=None).isoformat()) == []


def test_list_tasks_created_after_invalid(client):
    resp = client.get("/tasks", params={"created_after": "not-a-date"})
    assert resp.status_code == 422
