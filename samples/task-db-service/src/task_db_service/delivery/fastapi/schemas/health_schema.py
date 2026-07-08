from task_db_service.foundation.delivery.fastapi.schema import BaseFastAPISchema


class HealthResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for health checks.

    Example:
        HealthResponseSchema(status="ok")
    """

    status: str
