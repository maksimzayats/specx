from task_db_service.core.health.use_cases.check_health import CheckHealthQuery, CheckHealthUseCase


def test_execute_returns_health_status(check_health_use_case: CheckHealthUseCase) -> None:
    result = check_health_use_case.execute(query=CheckHealthQuery())

    assert result.status == "ok"
