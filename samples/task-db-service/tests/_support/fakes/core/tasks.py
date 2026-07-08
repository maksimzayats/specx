from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

from task_db_service.core.tasks.entities.task_entity import TaskEntity
from task_db_service.core.tasks.repositories.task_repository import TaskRepository
from task_db_service.core.tasks.repositories.task_unit_of_work import (
    TaskUnitOfWork,
    TaskUnitOfWorkManager,
)


@dataclass(kw_only=True, slots=True)
class InMemoryTaskRepository(TaskRepository):
    _tasks: dict[int, TaskEntity] = field(default_factory=dict)
    _next_id: int = 1

    async def add(self, *, title: str) -> TaskEntity:
        task = TaskEntity(id=self._next_id, title=title, is_completed=False)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    async def get(self, *, task_id: int) -> TaskEntity | None:
        return self._tasks.get(task_id)

    async def list(self) -> list[TaskEntity]:
        return [self._tasks[task_id] for task_id in sorted(self._tasks)]

    async def complete(self, *, task_id: int) -> TaskEntity | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None

        completed = TaskEntity(id=task.id, title=task.title, is_completed=True)
        self._tasks[task_id] = completed
        return completed

    def add_existing(
        self,
        *,
        title: str,
        is_completed: bool = False,
        task_id: int | None = None,
    ) -> TaskEntity:
        resolved_task_id = task_id or self._next_id
        task = TaskEntity(
            id=resolved_task_id,
            title=title,
            is_completed=is_completed,
        )
        self._tasks[task.id] = task
        self._next_id = max(self._next_id, task.id + 1)
        return task


@dataclass(kw_only=True, slots=True)
class InMemoryTaskUnitOfWork(TaskUnitOfWork):
    _tasks: TaskRepository

    @property
    def tasks(self) -> TaskRepository:
        return self._tasks


@dataclass(kw_only=True, slots=True)
class InMemoryTaskUnitOfWorkManager(TaskUnitOfWorkManager):
    repository: InMemoryTaskRepository = field(default_factory=InMemoryTaskRepository)
    entered_count: int = 0
    committed_count: int = 0
    rolled_back_count: int = 0
    exited_count: int = 0

    async def __aenter__(self) -> TaskUnitOfWork:
        self.entered_count += 1
        return InMemoryTaskUnitOfWork(_tasks=self.repository)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        _ = exc
        _ = traceback
        self.exited_count += 1
        if exc_type is None:
            self.committed_count += 1
        else:
            self.rolled_back_count += 1
        return False
