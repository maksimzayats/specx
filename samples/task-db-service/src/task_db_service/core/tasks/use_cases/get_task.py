from dataclasses import dataclass

from diwire import Injected
from specx.foundation.query import BaseQuery
from specx.foundation.use_case import BaseUseCase

from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.core.tasks.services.task_lookup_service import TaskLookupService


@dataclass(frozen=True, kw_only=True, slots=True)
class GetTaskQuery(BaseQuery):
    """Query for reading one task.

    Example:
        GetTaskQuery(task_id=1)
    """

    task_id: int


@dataclass(kw_only=True, slots=True)
class GetTaskUseCase(BaseUseCase):
    """Use case that reads one task through the task UoW manager.

    Example:
        task = await use_case.execute(query=GetTaskQuery(task_id=1))
    """

    _task_lookup_service: Injected[TaskLookupService]
    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, query: GetTaskQuery) -> TaskDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._task_lookup_service.get(
                unit_of_work=unit_of_work,
                task_id=query.task_id,
            )
