class BaseEffectService:
    """Base class for helpers that perform or coordinate side effects.

    Effect services may mutate owned state through an active unit of work
    passed by a use case, or call outbound gateways with real side effects.
    They must not open unit-of-work scopes, own transaction lifecycle, return
    entities outward, or import delivery/framework code.

    Example:
        class TaskCompletionService(BaseEffectService):
            async def complete(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
                task = await unit_of_work.tasks.complete(task_id=task_id)
                return TaskDTO.model_validate(task)
    """
