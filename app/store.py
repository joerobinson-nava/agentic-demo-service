"""In-memory task store.

Note for the agentic demo: `add` raises `DuplicateTaskError` on a repeated id.
The API layer does not yet handle it, so a duplicate id currently surfaces as an
HTTP 500. Ticket AGENTDEV-2 is to return 409 instead.
"""

from app.models import Status, Task, TaskCreate


class DuplicateTaskError(Exception):
    """Raised when adding a task whose id already exists."""


class UnknownTaskError(Exception):
    """Raised when a task or dependency id does not name a stored task."""

    def __init__(self, task_ids: list[int]) -> None:
        self.task_ids = sorted(set(task_ids))
        super().__init__(self.task_ids)


class DependencyCycleError(Exception):
    """Raised when a dependency would create a cycle.

    `cycle` is a list of ids that starts and ends with the same id.
    """

    def __init__(self, cycle: list[int]) -> None:
        self.cycle = list(cycle)
        super().__init__(self.cycle)


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

    def add(self, data: TaskCreate) -> Task:
        """Add a new task, raising DuplicateTaskError on a repeated id."""
        if data.id in self._tasks:
            raise DuplicateTaskError(data.id)
        deps = sorted(set(data.depends_on))
        if data.id in deps:
            raise DependencyCycleError([data.id, data.id])
        missing = [d for d in deps if d not in self._tasks]
        if missing:
            raise UnknownTaskError(missing)
        task = Task(id=data.id, title=data.title, status=data.status, depends_on=deps)
        self._tasks[data.id] = task
        return task

    def get(self, task_id: int) -> Task | None:
        """Return the task with the given id, or None if absent."""
        return self._tasks.get(task_id)

    def add_dependency(self, task_id: int, dependency_id: int) -> Task:
        """Make `task_id` depend on `dependency_id`, rejecting cycles."""
        missing = [i for i in (task_id, dependency_id) if i not in self._tasks]
        if missing:
            raise UnknownTaskError(missing)
        task = self._tasks[task_id]
        if dependency_id in task.depends_on:
            return task
        path = self._find_path(dependency_id, task_id)
        if path is not None:
            raise DependencyCycleError([task_id, *path])
        task.depends_on = sorted([*task.depends_on, dependency_id])
        return task

    def remove_dependency(self, task_id: int, dependency_id: int) -> None:
        """Remove one dependency from a task."""
        task = self._tasks.get(task_id)
        if task is None:
            raise UnknownTaskError([task_id])
        if dependency_id not in task.depends_on:
            raise UnknownTaskError([dependency_id])
        task.depends_on = [d for d in task.depends_on if d != dependency_id]

    def blockers(self, task_id: int) -> list[Task]:
        """Return the direct dependencies of a task that are not done, by id."""
        task = self._tasks.get(task_id)
        if task is None:
            raise UnknownTaskError([task_id])
        deps = (self._tasks.get(d) for d in task.depends_on)
        return [d for d in deps if d is not None and d.status != Status.done]

    def ready(self) -> list[Task]:
        """Return todo tasks whose direct dependencies are all done, by id."""
        return [
            task
            for _, task in sorted(self._tasks.items())
            if task.status == Status.todo
            and all(
                (dep := self._tasks.get(d)) is not None and dep.status == Status.done
                for d in task.depends_on
            )
        ]

    def _find_path(self, start: int, target: int) -> list[int] | None:
        """Return a dependency path [start, ..., target], or None if unreachable."""
        parents: dict[int, int | None] = {start: None}
        stack = [start]
        while stack:
            node = stack.pop()
            if node == target:
                path = []
                current: int | None = node
                while current is not None:
                    path.append(current)
                    current = parents[current]
                return path[::-1]
            for child in reversed(self._tasks[node].depends_on):
                if child not in parents:
                    parents[child] = node
                    stack.append(child)
        return None


store = TaskStore()
