from dataclasses import dataclass

from specx.core.foundation.pure_service import BasePureService

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthProbeDTO,
    HealthProbeStatusEnum,
)


@dataclass(kw_only=True, slots=True)
class LivenessProbeService(BasePureService):
    """Service that reports lightweight process liveness.

    Example:
        probe = service.report()
    """

    def report(self) -> HealthProbeDTO:
        return HealthProbeDTO(status=HealthProbeStatusEnum.PASS)
