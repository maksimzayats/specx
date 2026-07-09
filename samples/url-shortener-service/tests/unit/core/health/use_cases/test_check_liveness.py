from diwire import Container

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.use_cases.check_liveness import (
    CheckLivenessQuery,
    CheckLivenessUseCase,
)


def test_execute_returns_process_liveness(container: Container) -> None:
    use_case = container.resolve(CheckLivenessUseCase)

    result = use_case.execute(query=CheckLivenessQuery())

    assert result == HealthProbeDTO(status=HealthProbeStatusEnum.PASS)
