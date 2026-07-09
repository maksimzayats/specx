from dataclasses import dataclass

import pytest
from diwire import Container

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthCheckDTO,
    HealthCheckNameEnum,
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)
from url_shortener_service.core.health.services.readiness_probe_service import (
    ReadinessProbeService,
)


@dataclass(kw_only=True, slots=True)
class FakeReadinessCheckGateway(ReadinessCheckGateway):
    """Readiness gateway double for readiness service tests.

    Example:
        gateway = FakeReadinessCheckGateway(checks=())
    """

    checks: tuple[HealthCheckDTO, ...]

    async def check(self) -> tuple[HealthCheckDTO, ...]:
        return self.checks


@dataclass(frozen=True, kw_only=True, slots=True)
class ReadinessReportCase:
    id: str
    checks: tuple[HealthCheckDTO, ...]
    expected_status: HealthProbeStatusEnum


@pytest.mark.anyio
@pytest.mark.parametrize(
    "case",
    [
        ReadinessReportCase(
            id="all_checks_pass",
            checks=(
                HealthCheckDTO(
                    name=HealthCheckNameEnum.DATABASE,
                    status=HealthProbeStatusEnum.PASS,
                ),
            ),
            expected_status=HealthProbeStatusEnum.PASS,
        ),
        ReadinessReportCase(
            id="database_check_fails",
            checks=(
                HealthCheckDTO(
                    name=HealthCheckNameEnum.DATABASE,
                    status=HealthProbeStatusEnum.FAIL,
                ),
            ),
            expected_status=HealthProbeStatusEnum.FAIL,
        ),
    ],
    ids=lambda case: case.id,
)
async def test_report_combines_readiness_checks(
    case: ReadinessReportCase,
    container: Container,
) -> None:
    gateway = FakeReadinessCheckGateway(checks=case.checks)
    container.add_instance(gateway, provides=ReadinessCheckGateway)
    service = container.resolve(ReadinessProbeService)

    result = await service.report()

    assert result == HealthProbeDTO(status=case.expected_status, checks=case.checks)
