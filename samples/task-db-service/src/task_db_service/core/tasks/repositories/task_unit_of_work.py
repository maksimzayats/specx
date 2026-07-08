from abc import abstractmethod

from task_db_service.core.tasks.repositories.task_repository import TaskRepository
from task_db_service.foundation.unit_of_work import BaseUnitOfWork
from task_db_service.foundation.unit_of_work_manager import BaseUnitOfWorkManager


class TaskUnitOfWork(BaseUnitOfWork):
    """Active transaction boundary for task repositories.

    Example:
        task = await unit_of_work.tasks.get(task_id=1)
    """

    def _unit_of_work_marker(self) -> None:
        return None

    @property
    @abstractmethod
    def tasks(self) -> TaskRepository:
        raise NotImplementedError


class TaskUnitOfWorkManager(BaseUnitOfWorkManager[TaskUnitOfWork]):
    """Manager that opens active task units of work.

    Example:
        async with task_unit_of_work_manager as unit_of_work:
            task = await unit_of_work.tasks.get(task_id=1)
    """
