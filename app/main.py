"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `GET /tasks` has no `status` filter yet (target for AGENTDEV-1).
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from fastapi import FastAPI, HTTPException

from app.models import Task, TaskCreate, TaskUpdate
from app.store import store

app = FastAPI(title="Agentic Demo Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    """Return all tasks."""
    return store.list()


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
def update_task(task_id: int, data: TaskUpdate) -> Task:
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if data.title is not None:
        task.title = data.title
    if data.status is not None:
        task.status = data.status
    return task

