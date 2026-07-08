from abc import abstractmethod

from specx.foundation.repository import BaseRepository

from task_db_service.core.tasks.entities.task_entity import TaskEntity


class TaskRepository(BaseRepository):
    """Repository port for task persistence.

    Example:
        task = await repository.get(task_id=1)
    """

    @abstractmethod
    async def add(self, *, title: str) -> TaskEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, *, task_id: int) -> TaskEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[TaskEntity]:
        raise NotImplementedError

    @abstractmethod
    async def complete(self, *, task_id: int) -> TaskEntity | None:
        raise NotImplementedError
