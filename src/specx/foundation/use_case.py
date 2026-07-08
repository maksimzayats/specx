class BaseUseCase:
    """Base for externally meaningful application actions.

    Example:
        class CreateTaskUseCase(BaseUseCase):
            async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:
                return TaskDTO(id=1, title=command.title)
    """
