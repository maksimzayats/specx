from __future__ import annotations

from dataclasses import dataclass

from url_shortener_service.core.health.dtos.health_probe_dto import HealthCheckDTO
from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)


@dataclass(kw_only=True, slots=True)
class FakeReadinessCheckGateway(ReadinessCheckGateway):
    """Readiness gateway double for health unit tests.

    Example:
        gateway = FakeReadinessCheckGateway(checks=())
    """

    checks: tuple[HealthCheckDTO, ...]

    async def check(self) -> tuple[HealthCheckDTO, ...]:
        return self.checks
