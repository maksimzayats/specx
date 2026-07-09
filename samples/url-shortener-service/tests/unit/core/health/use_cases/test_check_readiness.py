import pytest
from diwire import Container

from tests.unit.core.health.gateways.fake_readiness_check_gateway import (
    FakeReadinessCheckGateway,
)
from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthCheckDTO,
    HealthCheckNameEnum,
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)
from url_shortener_service.core.health.use_cases.check_readiness import (
    CheckReadinessQuery,
    CheckReadinessUseCase,
)


@pytest.mark.anyio
async def test_execute_returns_readiness_report(container: Container) -> None:
    checks = (
        HealthCheckDTO(
            name=HealthCheckNameEnum.DATABASE,
            status=HealthProbeStatusEnum.FAIL,
        ),
    )
    gateway = FakeReadinessCheckGateway(checks=checks)
    container.add_instance(gateway, provides=ReadinessCheckGateway)
    use_case = container.resolve(CheckReadinessUseCase)

    result = await use_case.execute(query=CheckReadinessQuery())

    assert result == HealthProbeDTO(status=HealthProbeStatusEnum.FAIL, checks=checks)
