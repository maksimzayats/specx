class BaseEffectService:
    """Base for helpers that perform or coordinate side effects.

    Effect services may mutate owned state through an active unit of work passed
    by a use case, or call outbound gateways with real side effects. They must
    not open unit-of-work scopes or own transaction lifecycle.

    Example:
        class TaskCompletionService(BaseEffectService):
            async def complete(self, *, task_id: int) -> TaskDTO:
                return TaskDTO(id=task_id, title="Done")
    """
