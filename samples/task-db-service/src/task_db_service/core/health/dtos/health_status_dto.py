from task_db_service.foundation.dto import BaseDTO


class HealthStatusDTO(BaseDTO):
    """DTO returned by the health use case.

    Example:
        HealthStatusDTO(status="ok")
    """

    status: str
