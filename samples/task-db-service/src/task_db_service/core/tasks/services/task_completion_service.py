from dataclasses import dataclass

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork
from task_db_service.foundation.effect_service import BaseEffectService


@dataclass(kw_only=True, slots=True)
class TaskCompletionService(BaseEffectService):
    """Service that completes tasks inside an active task unit of work.

    Example:
        task = await service.complete(unit_of_work=unit_of_work, task_id=1)
    """

    async def complete(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
        task = await unit_of_work.tasks.complete(task_id=task_id)
        if task is None:
            raise TaskNotFoundError(task_id=task_id)
        return TaskDTO.model_validate(task)
