from dataclasses import dataclass

from diwire import Injected

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.foundation.command import BaseCommand
from task_db_service.foundation.use_case import BaseUseCase


class CompleteTaskCommand(BaseCommand):
    """Command for marking a task complete.

    Example:
        CompleteTaskCommand(task_id=1)
    """

    task_id: int


@dataclass(kw_only=True, slots=True)
class CompleteTaskUseCase(BaseUseCase):
    """Use case that marks a task complete through the task UoW manager.

    Example:
        task = await use_case.execute(command=CompleteTaskCommand(task_id=1))
    """

    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, command: CompleteTaskCommand) -> TaskDTO:
        async with self._unit_of_work_manager as unit_of_work:
            task = await unit_of_work.tasks.complete(task_id=command.task_id)
        if task is None:
            raise TaskNotFoundError(task_id=command.task_id)
        return TaskDTO.model_validate(task)
