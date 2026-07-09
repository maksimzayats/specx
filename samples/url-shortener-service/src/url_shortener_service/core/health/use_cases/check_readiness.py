from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.query import BaseQuery
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.health.dtos.health_probe_dto import HealthProbeDTO
from url_shortener_service.core.health.services.readiness_probe_service import (
    ReadinessProbeService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class CheckReadinessQuery(BaseQuery):
    """Query for checking whether the instance can receive traffic.

    Example:
        CheckReadinessQuery()
    """


@dataclass(kw_only=True, slots=True)
class CheckReadinessUseCase(BaseUseCase):
    """Use case that reports runtime readiness for delivery probe endpoints.

    Example:
        probe = await use_case.execute(query=CheckReadinessQuery())
    """

    _readiness_probe_service: Injected[ReadinessProbeService]

    async def execute(self, *, query: CheckReadinessQuery) -> HealthProbeDTO:
        _ = query

        return await self._readiness_probe_service.report()
