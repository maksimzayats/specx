from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.query import BaseQuery
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.health.dtos.health_probe_dto import HealthProbeDTO
from url_shortener_service.core.health.services.liveness_probe_service import (
    LivenessProbeService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class CheckLivenessQuery(BaseQuery):
    """Query for checking lightweight process liveness.

    Example:
        CheckLivenessQuery()
    """


@dataclass(kw_only=True, slots=True)
class CheckLivenessUseCase(BaseUseCase):
    """Use case that reports process liveness for delivery probe endpoints.

    Example:
        probe = use_case.execute(query=CheckLivenessQuery())
    """

    _liveness_probe_service: Injected[LivenessProbeService]

    def execute(self, *, query: CheckLivenessQuery) -> HealthProbeDTO:
        _ = query

        return self._liveness_probe_service.report()
