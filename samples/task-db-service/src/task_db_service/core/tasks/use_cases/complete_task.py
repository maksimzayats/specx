from dataclasses import dataclass

from diwire import Injected

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.core.tasks.services.task_completion_service import TaskCompletionService
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

    _task_completion_service: Injected[TaskCompletionService]
    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, command: CompleteTaskCommand) -> TaskDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._task_completion_service.complete(
                unit_of_work=unit_of_work,
                task_id=command.task_id,
            )
