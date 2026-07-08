from task_db_service.core.health.services.health_reporter_service import HealthReporterService
from task_db_service.core.health.use_cases.check_health import CheckHealthQuery, CheckHealthUseCase


def test_check_health_returns_ok() -> None:
    use_case = CheckHealthUseCase(
        _health_reporter_service=HealthReporterService(),
    )

    result = use_case.execute(query=CheckHealthQuery())

    assert result.status == "ok"
