from dataclasses import dataclass

from specx.foundation.entity import BaseEntity


@dataclass(frozen=True, kw_only=True, slots=True)
class TaskEntity(BaseEntity):
    """Framework-free task state used inside the core boundary.

    Example:
        TaskEntity(id=1, title="Ship skill", is_completed=False)
    """

    id: int
    title: str
    is_completed: bool
