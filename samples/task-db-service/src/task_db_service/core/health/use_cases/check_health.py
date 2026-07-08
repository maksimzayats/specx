from dataclasses import dataclass

from diwire import Injected
from specx.foundation.query import BaseQuery
from specx.foundation.use_case import BaseUseCase

from task_db_service.core.health.dtos.health_status_dto import HealthStatusDTO
from task_db_service.core.health.services.health_reporter_service import HealthReporterService


@dataclass(frozen=True, kw_only=True, slots=True)
class CheckHealthQuery(BaseQuery):
    """Query for reading application health status.

    Example:
        CheckHealthQuery()
    """


@dataclass(kw_only=True, slots=True)
class CheckHealthUseCase(BaseUseCase):
    """Use case that exposes health status to delivery.

    Example:
        CheckHealthUseCase(
            _health_reporter_service=HealthReporterService(),
        ).execute(query=CheckHealthQuery())
    """

    _health_reporter_service: Injected[HealthReporterService]

    def execute(self, *, query: CheckHealthQuery) -> HealthStatusDTO:
        _ = query
        return self._health_reporter_service.check()
