from diwire import Container

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.services.liveness_probe_service import (
    LivenessProbeService,
)


def test_report_returns_process_liveness(container: Container) -> None:
    service = container.resolve(LivenessProbeService)

    result = service.report()

    assert result == HealthProbeDTO(status=HealthProbeStatusEnum.PASS)
