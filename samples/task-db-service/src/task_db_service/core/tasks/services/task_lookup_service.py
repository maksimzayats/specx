from dataclasses import dataclass

from specx.foundation.read_service import BaseReadService

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.dtos.task_list_dto import TaskListDTO
from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork


@dataclass(kw_only=True, slots=True)
class TaskLookupService(BaseReadService):
    """Service that reads task DTOs from an active task unit of work.

    Example:
        task = await service.get(unit_of_work=unit_of_work, task_id=1)
    """

    async def get(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
        task = await unit_of_work.tasks.get(task_id=task_id)
        if task is None:
            raise TaskNotFoundError(task_id=task_id)
        return TaskDTO(id=task.id, title=task.title, is_completed=task.is_completed)

    async def list(self, *, unit_of_work: TaskUnitOfWork) -> TaskListDTO:
        tasks = await unit_of_work.tasks.list()
        return TaskListDTO(
            tasks=[
                TaskDTO(id=task.id, title=task.title, is_completed=task.is_completed)
                for task in tasks
            ],
        )
