from dataclasses import dataclass

from diwire import Injected

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)
from task_db_service.foundation.effect_service import BaseEffectService


@dataclass(kw_only=True, slots=True)
class TaskCreationService(BaseEffectService):
    """Service that creates tasks inside an active task unit of work.

    Example:
        task = await service.create(unit_of_work=unit_of_work, title="Ship skill")
    """

    _task_title_normalizer_service: Injected[TaskTitleNormalizerService]

    async def create(self, *, unit_of_work: TaskUnitOfWork, title: str) -> TaskDTO:
        normalized_title = self._task_title_normalizer_service.normalize(title=title)
        task = await unit_of_work.tasks.add(title=normalized_title)
        return TaskDTO.model_validate(task)
