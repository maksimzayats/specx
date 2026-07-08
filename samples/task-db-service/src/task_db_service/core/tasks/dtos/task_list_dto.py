from dataclasses import dataclass

from specx.foundation.dto import BaseDTO

from task_db_service.core.tasks.dtos.task_dto import TaskDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class TaskListDTO(BaseDTO):
    """DTO returned by task list use cases.

    Example:
        TaskListDTO(tasks=[TaskDTO(id=1, title="Ship skill", is_completed=False)])
    """

    tasks: list[TaskDTO]
