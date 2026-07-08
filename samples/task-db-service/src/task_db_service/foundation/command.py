from task_db_service.foundation.dto import BaseDTO


class BaseCommand(BaseDTO):
    """Base for use-case inputs that request state-changing work.

    Example:
        class CreateTaskCommand(BaseCommand):
            title: str
    """
