class BaseReadService:
    """Base for read-only orchestration helpers.

    Read services may read from repositories or read gateways, usually through
    an active unit of work passed by the caller. They may map entities to DTOs,
    but must not commit, roll back, publish, send email, or call write APIs.

    Example:
        class TaskLookupService(BaseReadService):
            async def get(self, *, task_id: int) -> TaskDTO:
                return TaskDTO(id=task_id, title="Ship")
    """
