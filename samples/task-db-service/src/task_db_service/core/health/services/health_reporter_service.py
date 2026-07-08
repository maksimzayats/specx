from dataclasses import dataclass

from specx.foundation.pure_service import BasePureService

from task_db_service.core.health.dtos.health_status_dto import HealthStatusDTO


@dataclass(kw_only=True, slots=True)
class HealthReporterService(BasePureService):
    """Service that returns deterministic application health status.

    Example:
        HealthReporterService().check()
    """

    def check(self) -> HealthStatusDTO:
        return HealthStatusDTO(status="ok")
