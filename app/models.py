"""Domain models for the demo task service."""

from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    """Lifecycle state of a task."""

    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskCreate(BaseModel):
    """Payload accepted when creating a task."""

    id: int
    title: str
    status: Status = Status.todo


class TaskUpdate(BaseModel):
    """Payload accepted when updating a task."""

    title: str | None = None
    status: Status | None = None


class Task(BaseModel):
    """A task stored by the service."""

    id: int
    title: str
    status: Status
