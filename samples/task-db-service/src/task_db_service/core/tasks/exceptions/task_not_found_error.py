from dataclasses import dataclass

from specx.foundation.exceptions import BaseApplicationError


@dataclass(kw_only=True)
class TaskNotFoundError(BaseApplicationError):
    """Raised when a requested task does not exist.

    Example:
        raise TaskNotFoundError(task_id=1)
    """

    task_id: int
