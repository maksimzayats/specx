from task_db_service.foundation.dto import BaseDTO


class TaskDTO(BaseDTO):
    """DTO returned to callers for task state.

    Example:
        TaskDTO(id=1, title="Ship skill", is_completed=False)
    """

    id: int
    title: str
    is_completed: bool
