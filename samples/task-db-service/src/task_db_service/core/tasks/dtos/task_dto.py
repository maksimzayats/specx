from dataclasses import dataclass

from specx.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class TaskDTO(BaseDTO):
    """DTO returned to callers for task state.

    Example:
        TaskDTO(id=1, title="Ship skill", is_completed=False)
    """

    id: int
    title: str
    is_completed: bool
