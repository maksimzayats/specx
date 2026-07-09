from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema

from url_shortener_service.core.health.dtos.health_probe_dto import HealthProbeStatusEnum


class ProbeCheckResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for one readiness dependency check.

    Example:
        ProbeCheckResponseSchema(status=HealthProbeStatusEnum.PASS)
    """

    status: HealthProbeStatusEnum


class ProbeResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for operational probe endpoints.

    Example:
        ProbeResponseSchema(status=HealthProbeStatusEnum.PASS)
    """

    status: HealthProbeStatusEnum
    checks: dict[str, ProbeCheckResponseSchema] | None = None
