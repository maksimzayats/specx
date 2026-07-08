from abc import abstractmethod

from task_db_service.core.tasks.entities.task_entity import TaskEntity
from task_db_service.foundation.repository import BaseRepository


class TaskRepository(BaseRepository):
    """Repository port for task persistence.

    Example:
        task = await repository.get(task_id=1)
    """

    def _repository_marker(self) -> None:
        return None

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
