class BaseReadService:
    """Base class for read-only orchestration helpers.

    Read services may read from repositories or read gateways, usually through
    an active unit of work passed by the caller. They may map entities to DTOs,
    but they must not commit, roll back, call repository mutators, publish
    messages, send email, charge money, or call external write APIs.

    Example:
        class TaskLookupService(BaseReadService):
            async def get(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
                task = await unit_of_work.tasks.get(task_id=task_id)
                return TaskDTO.model_validate(task)
    """
