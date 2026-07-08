from task_db_service.core.tasks.dtos.task_dto import TaskDTO
from task_db_service.foundation.dto import BaseDTO


class TaskListDTO(BaseDTO):
    """DTO returned by task list use cases.

    Example:
        TaskListDTO(tasks=[TaskDTO(id=1, title="Ship skill", is_completed=False)])
    """

    tasks: list[TaskDTO]
