from dataclasses import dataclass

from diwire import Injected
from specx.foundation.command import BaseCommand
from specx.foundation.use_case import BaseUseCase

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.core.tasks.services.task_creation_service import TaskCreationService


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateTaskCommand(BaseCommand):
    """Command for creating a task.

    Example:
        CreateTaskCommand(title="Ship skill")
    """

    title: str


@dataclass(kw_only=True, slots=True)
class CreateTaskUseCase(BaseUseCase):
    """Use case that creates a task through the task UoW manager.

    Example:
        task = await use_case.execute(command=CreateTaskCommand(title="Ship skill"))
    """

    _task_creation_service: Injected[TaskCreationService]
    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._task_creation_service.create(
                unit_of_work=unit_of_work,
                title=command.title,
            )
