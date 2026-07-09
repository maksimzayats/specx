from abc import ABC


class BaseRepository(ABC):  # noqa: B024
    """Base for core repository ports and their infrastructure adapters.

    Example:
        class TaskRepository(BaseRepository):
            async def get(self, *, task_id: int) -> TaskEntity | None:
                return None
    """
