"""Domain models for the demo task service."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


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
    depends_on: list[int] = Field(default_factory=list)


class Task(BaseModel):
    """A task stored by the service."""

    id: int
    title: str
    status: Status
    depends_on: list[int] = Field(default_factory=list)

    @field_validator("depends_on")
    @classmethod
    def _sorted_unique(cls, value: list[int]) -> list[int]:
        return sorted(set(value))


class DependencyAdd(BaseModel):
    """Payload accepted when adding a dependency to a task."""

    depends_on: int
