class BaseApplicationError(Exception):
    """Base for application errors translated by delivery layers.

    Example:
        class TaskNotFoundError(BaseApplicationError):
            task_id: int
    """


class BaseApplicationValueError(ValueError):
    """Base for invalid application values rejected before persistence.

    Example:
        class InvalidTaskTitleValueError(BaseApplicationValueError):
            title: str
    """
