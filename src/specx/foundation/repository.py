class BaseRepository:
    """Base for core repository ports and their infrastructure adapters.

    Example:
        class TaskRepository(BaseRepository):
            async def get(self, *, task_id: int) -> TaskEntity | None:
                return None
    """
