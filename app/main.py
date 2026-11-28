"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `GET /tasks` has no `status` filter yet (target for AGENTDEV-1).
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Query

from app.models import Task, TaskCreate
from app.store import store

app = FastAPI(title="Agentic Demo Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    created_after: datetime | None = Query(
        default=None,
        description=(
            "ISO 8601 time; return only tasks created strictly after it. "
            "A time without an offset is treated as UTC."
        ),
    ),
) -> list[Task]:
    """Return all tasks, optionally only those created after a given time."""
    if created_after is not None and created_after.tzinfo is None:
        created_after = created_after.replace(tzinfo=UTC)
    return store.list(created_after=created_after)


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
