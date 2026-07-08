from __future__ import annotations

import pytest
from diwire import Container

from task_db_service.core.health.services.health_reporter_service import HealthReporterService
from task_db_service.core.health.use_cases.check_health import CheckHealthUseCase
from task_db_service.ioc.container import get_container


@pytest.fixture
def container() -> Container:
    return get_container()


@pytest.fixture
def health_reporter_service(container: Container) -> HealthReporterService:
    return container.resolve(HealthReporterService)


@pytest.fixture
def check_health_use_case(container: Container) -> CheckHealthUseCase:
    return container.resolve(CheckHealthUseCase)
