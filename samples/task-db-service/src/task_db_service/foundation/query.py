from task_db_service.foundation.dto import BaseDTO


class BaseQuery(BaseDTO):
    """Base for use-case inputs that request read-only results.

    Example:
        class GetTaskQuery(BaseQuery):
            task_id: int
    """
