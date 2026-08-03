"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from fastapi import FastAPI, HTTPException, Query

from app.models import Status, Task, TaskCreate
from app.store import store

app = FastAPI(title="Agentic Demo Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(status: Status | None = Query(None, description="Filter tasks by status")) -> list[Task]:
    """Return all tasks, optionally filtered by status."""
    tasks = store.list()
    if status is not None:
        tasks = [task for task in tasks if task.status == status]
    return tasks


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
