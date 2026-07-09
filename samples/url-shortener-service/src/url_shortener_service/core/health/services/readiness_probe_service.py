from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.read_service import BaseReadService

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)


@dataclass(kw_only=True, slots=True)
class ReadinessProbeService(BaseReadService):
    """Service that reports whether required runtime dependencies are ready.

    Example:
        probe = await service.report()
    """

    _readiness_check_gateway: Injected[ReadinessCheckGateway]

    async def report(self) -> HealthProbeDTO:
        checks = await self._readiness_check_gateway.check()
        status = (
            HealthProbeStatusEnum.PASS
            if all(check.status == HealthProbeStatusEnum.PASS for check in checks)
            else HealthProbeStatusEnum.FAIL
        )

        return HealthProbeDTO(status=status, checks=checks)
