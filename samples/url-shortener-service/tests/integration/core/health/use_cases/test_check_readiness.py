import pytest
from diwire import Container

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthCheckDTO,
    HealthCheckNameEnum,
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.use_cases.check_readiness import (
    CheckReadinessQuery,
    CheckReadinessUseCase,
)


@pytest.mark.anyio
async def test_execute_reports_database_ready(container: Container) -> None:
    use_case = container.resolve(CheckReadinessUseCase)

    result = await use_case.execute(query=CheckReadinessQuery())

    assert result == HealthProbeDTO(
        status=HealthProbeStatusEnum.PASS,
        checks=(
            HealthCheckDTO(
                name=HealthCheckNameEnum.DATABASE,
                status=HealthProbeStatusEnum.PASS,
            ),
        ),
    )
