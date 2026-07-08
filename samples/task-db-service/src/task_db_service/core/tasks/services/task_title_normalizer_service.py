from dataclasses import dataclass

from specx.foundation.pure_service import BasePureService

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)


@dataclass(kw_only=True, slots=True)
class TaskTitleNormalizerService(BasePureService):
    """Service that normalizes and validates task titles.

    Example:
        TaskTitleNormalizerService().normalize(title="  Ship   skill  ")
    """

    def normalize(self, *, title: str) -> str:
        normalized = " ".join(title.split())
        if normalized == "":
            raise InvalidTaskTitleValueError(title=title)
        return normalized
