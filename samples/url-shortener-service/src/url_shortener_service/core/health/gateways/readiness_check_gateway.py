from abc import abstractmethod

from specx.core.foundation.gateway import BaseGateway

from url_shortener_service.core.health.dtos.health_probe_dto import HealthCheckDTO


class ReadinessCheckGateway(BaseGateway):
    """Gateway that checks runtime dependencies required for serving traffic.

    External effect: checks configured runtime infrastructure readiness.

    Example:
        checks = await gateway.check()
    """

    @abstractmethod
    async def check(self) -> tuple[HealthCheckDTO, ...]:
        raise NotImplementedError
