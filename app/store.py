"""In-memory task store.

Note for the agentic demo: `add` raises `DuplicateTaskError` on a repeated id.
The API layer does not yet handle it, so a duplicate id currently surfaces as an
HTTP 500. Ticket AGENTDEV-2 is to return 409 instead.
"""

from __future__ import annotations

from app.models import Status, Task, TaskCreate, TaskUpdate


class DuplicateTaskError(Exception):
    """Raised when adding a task whose id already exists."""


class TaskStore:
    """A simple in-memory task store keyed by task id."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}

    def clear(self) -> None:
        """Remove all tasks. Used to isolate tests."""
        self._tasks.clear()

    def list(self) -> list[Task]:
        """Return all tasks in insertion order."""
        return list(self._tasks.values())

    def list_by_status(self, status: Status) -> list[Task]:
        """Return all tasks with the given status."""
        return [task for task in self._tasks.values() if task.status == status]

    def add(self, data: TaskCreate) -> Task:
        """Add a new task, raising DuplicateTaskError on a repeated id."""
        if data.id in self._tasks:
            raise DuplicateTaskError(data.id)
        task = Task(id=data.id, title=data.title, status=data.status)
        self._tasks[data.id] = task
        return task

    def get(self, task_id: int) -> Task | None:
        """Return the task with the given id, or None if absent."""
        return self._tasks.get(task_id)

    def update(self, task_id: int, data: TaskUpdate) -> Task | None:
        """Update an existing task, returning the updated task or None if not found."""
        if task_id not in self._tasks:
            return None
        task = Task(id=task_id, title=data.title, status=data.status)
        self._tasks[task_id] = task
        return task

    def delete(self, task_id: int) -> bool:
        """Delete a task by id, returning True if deleted or False if not found."""
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True


store = TaskStore()
