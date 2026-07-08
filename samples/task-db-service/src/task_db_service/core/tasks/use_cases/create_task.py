from dataclasses import dataclass

from diwire import Injected

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)
from task_db_service.foundation.command import BaseCommand
from task_db_service.foundation.use_case import BaseUseCase


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

    _task_title_normalizer_service: Injected[TaskTitleNormalizerService]
    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:
        title = self._task_title_normalizer_service.normalize(title=command.title)
        async with self._unit_of_work_manager as unit_of_work:
            task = await unit_of_work.tasks.add(title=title)
        return TaskDTO.model_validate(task)
