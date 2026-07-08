from dataclasses import dataclass

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.foundation.service import BaseService


@dataclass(kw_only=True, slots=True)
class TaskTitleNormalizerService(BaseService):
    """Service that normalizes and validates task titles.

    Example:
        TaskTitleNormalizerService().normalize(title="  Ship   skill  ")
    """

    def normalize(self, *, title: str) -> str:
        normalized = " ".join(title.split())
        if normalized == "":
            raise InvalidTaskTitleValueError(title=title)
        return normalized
