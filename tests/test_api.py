"""API tests covering current (baseline) behavior.

These tests are all green on the baseline. They intentionally do not cover the
`status` filter (AGENTDEV-1) or the duplicate-id case (AGENTDEV-2); those are
added by the agentic platform as part of the demo.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import TaskCreate
from app.store import DependencyCycleError, TaskStore, UnknownTaskError, store


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
    expected = {**payload, "depends_on": []}
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


def make(client, task_id, status="todo", depends_on=None):
    body = {"id": task_id, "title": f"t{task_id}", "status": status}
    if depends_on is not None:
        body["depends_on"] = depends_on
    resp = client.post("/tasks", json=body)
    assert resp.status_code == 201
    return resp.json()


def test_depends_on_defaults_empty_and_is_normalized(client):
    assert make(client, 1)["depends_on"] == []
    make(client, 2)
    make(client, 3)
    created = make(client, 4, depends_on=[3, 2, 3])
    assert created["depends_on"] == [2, 3]
    assert client.get("/tasks/4").json()["depends_on"] == [2, 3]
    assert [t["depends_on"] for t in client.get("/tasks").json()] == [[], [], [], [2, 3]]


def test_create_with_unknown_dependencies_returns_422(client):
    make(client, 1)
    resp = client.post("/tasks", json={"id": 2, "title": "x", "depends_on": [99, 1, 42]})
    assert resp.status_code == 422
    assert resp.json()["detail"]["missing_ids"] == [42, 99]
    assert client.get("/tasks/2").status_code == 404


def test_create_with_self_dependency_returns_422(client):
    resp = client.post("/tasks", json={"id": 5, "title": "x", "depends_on": [5]})
    assert resp.status_code == 422
    assert client.get("/tasks").json() == []


def test_add_dependency(client):
    make(client, 1)
    make(client, 2)
    make(client, 3)
    resp = client.post("/tasks/3/dependencies", json={"depends_on": 2})
    assert resp.status_code == 200
    assert resp.json()["depends_on"] == [2]
    resp = client.post("/tasks/3/dependencies", json={"depends_on": 1})
    assert resp.json()["depends_on"] == [1, 2]


def test_add_dependency_is_idempotent(client):
    make(client, 1)
    make(client, 2)
    first = client.post("/tasks/2/dependencies", json={"depends_on": 1})
    second = client.post("/tasks/2/dependencies", json={"depends_on": 1})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert second.json()["depends_on"] == [1]


def test_add_dependency_unknown_task_returns_404(client):
    make(client, 1)
    assert client.post("/tasks/9/dependencies", json={"depends_on": 1}).status_code == 404
    assert client.post("/tasks/1/dependencies", json={"depends_on": 9}).status_code == 404
    assert client.post("/tasks/8/dependencies", json={"depends_on": 9}).status_code == 404


def test_add_self_dependency_returns_409(client):
    make(client, 1)
    resp = client.post("/tasks/1/dependencies", json={"depends_on": 1})
    assert resp.status_code == 409
    assert resp.json()["detail"]["cycle"] == [1, 1]
    assert client.get("/tasks/1").json()["depends_on"] == []


def test_add_two_task_cycle_returns_409(client):
    make(client, 1)
    make(client, 2, depends_on=[1])
    resp = client.post("/tasks/1/dependencies", json={"depends_on": 2})
    assert resp.status_code == 409
    assert resp.json()["detail"]["cycle"] == [1, 2, 1]
    assert client.get("/tasks/1").json()["depends_on"] == []


def test_add_three_task_cycle_returns_409(client):
    make(client, 3)
    make(client, 2, depends_on=[3])
    make(client, 1, depends_on=[2])
    resp = client.post("/tasks/3/dependencies", json={"depends_on": 1})
    assert resp.status_code == 409
    assert resp.json()["detail"]["cycle"] == [3, 1, 2, 3]
    assert client.get("/tasks/3").json()["depends_on"] == []


def test_diamond_is_not_a_cycle(client):
    make(client, 1)
    make(client, 2, depends_on=[1])
    make(client, 3, depends_on=[1])
    make(client, 4, depends_on=[2])
    resp = client.post("/tasks/4/dependencies", json={"depends_on": 3})
    assert resp.status_code == 200
    assert resp.json()["depends_on"] == [2, 3]


def test_remove_dependency(client):
    make(client, 1)
    make(client, 2, depends_on=[1])
    resp = client.delete("/tasks/2/dependencies/1")
    assert resp.status_code == 204
    assert client.get("/tasks/2").json()["depends_on"] == []
    assert client.delete("/tasks/2/dependencies/1").status_code == 404


def test_remove_dependency_404s(client):
    make(client, 1)
    make(client, 2)
    assert client.delete("/tasks/9/dependencies/1").status_code == 404
    assert client.delete("/tasks/2/dependencies/1").status_code == 404


def test_blockers_filters_and_orders(client):
    make(client, 2, status="done")
    make(client, 4, status="in_progress")
    make(client, 5, status="todo")
    make(client, 6, status="done")
    make(client, 1, depends_on=[5, 2, 4, 6])
    resp = client.get("/tasks/1/blockers")
    assert resp.status_code == 200
    assert [t["id"] for t in resp.json()] == [4, 5]


def test_blockers_empty_and_missing(client):
    make(client, 1)
    assert client.get("/tasks/1/blockers").json() == []
    assert client.get("/tasks/9/blockers").status_code == 404


def test_ready_queue(client):
    make(client, 9, status="done")
    make(client, 8, status="done")
    make(client, 7, status="in_progress")
    make(client, 6, depends_on=[9, 8])
    make(client, 5, depends_on=[9, 7])
    make(client, 4)
    make(client, 3, status="done", depends_on=[9])
    make(client, 2, status="in_progress")
    resp = client.get("/tasks/ready")
    assert resp.status_code == 200
    assert [t["id"] for t in resp.json()] == [4, 6]


def test_ready_route_is_not_parsed_as_task_id(client):
    resp = client.get("/tasks/ready")
    assert resp.status_code == 200
    assert resp.json() == []


def test_store_errors_carry_details():
    local = TaskStore()
    local.add(TaskCreate(id=1, title="a"))
    with pytest.raises(UnknownTaskError) as unknown:
        local.add_dependency(1, 7)
    assert unknown.value.task_ids == [7]
    with pytest.raises(DependencyCycleError) as cycle:
        local.add_dependency(1, 1)
    assert cycle.value.cycle == [1, 1]
