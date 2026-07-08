from task_db_service.foundation.delivery.fastapi.schema import BaseFastAPISchema


class CreateTaskRequestSchema(BaseFastAPISchema):
    """FastAPI request schema for task creation.

    Example:
        CreateTaskRequestSchema(title="Ship skill")
    """

    title: str


class TaskResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for one task.

    Example:
        TaskResponseSchema(id=1, title="Ship skill", is_completed=False)
    """

    id: int
    title: str
    is_completed: bool


class TaskListResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for task lists.

    Example:
        TaskListResponseSchema(
            tasks=[TaskResponseSchema(id=1, title="Ship skill", is_completed=False)],
        )
    """

    tasks: list[TaskResponseSchema]
