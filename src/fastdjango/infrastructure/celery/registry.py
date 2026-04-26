import asyncio
from dataclasses import dataclass
from typing import Any

from celery import Celery, Task
from celery.result import AsyncResult


class TaskNotFoundError(Exception):
    pass


@dataclass(kw_only=True)
class CeleryTask[**P, R]:
    task: Task[P, R]

    @property
    def name(self) -> str:
        return self.task.name

    @property
    def raw(self) -> Task[P, R]:
        return self.task

    def delay(self, *args: P.args, **kwargs: P.kwargs) -> AsyncResult[R]:
        return self.task.delay(*args, **kwargs)

    async def adelay(self, *args: P.args, **kwargs: P.kwargs) -> AsyncResult[R]:
        return await asyncio.to_thread(self.delay, *args, **kwargs)

    def apply_async(self, *args: Any, **kwargs: Any) -> AsyncResult[R]:
        return self.task.apply_async(*args, **kwargs)

    async def aapply_async(self, *args: Any, **kwargs: Any) -> AsyncResult[R]:
        return await asyncio.to_thread(self.apply_async, *args, **kwargs)


@dataclass(kw_only=True)
class BaseTasksRegistry:
    _celery_app: Celery

    def _get_task_by_name[**P, R](self, name: str) -> CeleryTask[P, R]:
        try:
            task = self._celery_app.tasks[name]
        except KeyError as e:
            msg = f"Task with name '{name}' not found in registry."
            raise TaskNotFoundError(msg) from e

        return CeleryTask(task=task)
