from dataclasses import dataclass

from diwire import Injected

from task_db_service.core.tasks.dtos.task_list_dto import TaskListDTO
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager
from task_db_service.core.tasks.services.task_lookup_service import TaskLookupService
from task_db_service.foundation.query import BaseQuery
from task_db_service.foundation.use_case import BaseUseCase


class ListTasksQuery(BaseQuery):
    """Query for reading all tasks.

    Example:
        ListTasksQuery()
    """


@dataclass(kw_only=True, slots=True)
class ListTasksUseCase(BaseUseCase):
    """Use case that reads all tasks through the task UoW manager.

    Example:
        result = await use_case.execute(query=ListTasksQuery())
    """

    _task_lookup_service: Injected[TaskLookupService]
    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]

    async def execute(self, *, query: ListTasksQuery) -> TaskListDTO:
        _ = query
        async with self._unit_of_work_manager as unit_of_work:
            return await self._task_lookup_service.list(unit_of_work=unit_of_work)
