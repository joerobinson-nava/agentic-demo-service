"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `GET /tasks` has no `status` filter yet (target for AGENTDEV-1).
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from fastapi import FastAPI, HTTPException, Query

from app.models import Task, TaskCreate, TaskUpdate, Status
from app.store import store

app = FastAPI(title="Agentic Demo Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(status: Status | None = Query(default=None)) -> list[Task]:
    """Return all tasks, optionally filtered by status."""
    tasks = store.list()
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    return tasks


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(data: TaskCreate) -> Task:
    """Create a task."""
    return store.add(data)


@app.get("/tasks/count")
def count_tasks(status: Status | None = Query(default=None)) -> dict[str, int]:
    """Return count of tasks, optionally filtered by status."""
    return {"count": store.count_by_status(status)}


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    """Return a single task by id."""
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, data: TaskUpdate) -> Task:
    """Update a task partially. Returns 404 if not found."""
    updated = store.update(task_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    """Delete a task. Returns 204 on success, 404 if not found."""
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
