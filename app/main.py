"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `GET /tasks` has no `status` filter yet (target for AGENTDEV-1).
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from typing import Optional

from fastapi import FastAPI, HTTPException

from app.models import Status, Task, TaskCreate, TaskUpdate
from app.store import store

app = FastAPI(title="Agentic Demo Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(status: Status | None = None) -> list[Task]:
    """Return all tasks, optionally filtered by status."""
    return [t for t in store.list() if status is None or t.status == status]


@app.get("/tasks/count")
def count_tasks(status: Status | None = None) -> dict[str, int]:
    """Return the count of tasks, optionally filtered by status."""
    return {"count": store.count_by_status(status)}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(data: TaskCreate) -> Task:
    """Create a task."""
    return store.add(data)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    """Return a single task by id."""
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, update: TaskUpdate) -> Task:
    """Update a task."""
    updated = store.update(task_id, update)
    if not updated:
        raise HTTPException(404, "Task not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    """Delete a task."""
    if not store.delete(task_id):
        raise HTTPException(404, "Task not found")
