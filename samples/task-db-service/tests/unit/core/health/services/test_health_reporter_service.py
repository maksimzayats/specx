from task_db_service.core.health.services.health_reporter_service import HealthReporterService


def test_check_returns_ok_status(health_reporter_service: HealthReporterService) -> None:
    result = health_reporter_service.check()

    assert result.status == "ok"
