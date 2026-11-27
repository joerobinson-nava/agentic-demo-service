"""FastAPI application for the demo task service.

Demo seams for the agentic platform:
- `GET /tasks` has no `status` filter yet (target for AGENTDEV-1).
- `POST /tasks` does not handle a duplicate id, so it returns 500 today
  (target for AGENTDEV-2).
"""

from fastapi import FastAPI, HTTPException, Response

from app.models import DependencyAdd, Task, TaskCreate
from app.store import DependencyCycleError, UnknownTaskError, store

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
    try:
        return store.add(data)
    except UnknownTaskError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Unknown dependency ids", "missing_ids": exc.task_ids},
        ) from exc
    except DependencyCycleError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Task cannot depend on itself", "cycle": exc.cycle},
        ) from exc


# Declared before `/tasks/{task_id}` so "ready" is never parsed as a task id.
@app.get("/tasks/ready", response_model=list[Task])
def ready_tasks() -> list[Task]:
    """Return todo tasks whose direct dependencies are all done."""
    return store.ready()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    """Return a single task by id."""
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/{task_id}/dependencies", response_model=Task)
def add_dependency(task_id: int, data: DependencyAdd) -> Task:
    """Add one dependency to a task."""
    try:
        return store.add_dependency(task_id, data.depends_on)
    except UnknownTaskError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except DependencyCycleError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": "Dependency would create a cycle", "cycle": exc.cycle},
        ) from exc


@app.delete("/tasks/{task_id}/dependencies/{dependency_id}", status_code=204)
def remove_dependency(task_id: int, dependency_id: int) -> Response:
    """Remove one dependency from a task."""
    try:
        store.remove_dependency(task_id, dependency_id)
    except UnknownTaskError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return Response(status_code=204)


@app.get("/tasks/{task_id}/blockers", response_model=list[Task])
def task_blockers(task_id: int) -> list[Task]:
    """Return the direct dependencies of a task that are not done."""
    try:
        return store.blockers(task_id)
    except UnknownTaskError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
