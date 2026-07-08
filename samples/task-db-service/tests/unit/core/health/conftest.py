from __future__ import annotations

import pytest
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy

from task_db_service.core.health.services.health_reporter_service import HealthReporterService
from task_db_service.core.health.use_cases.check_health import CheckHealthUseCase


@pytest.fixture
def container() -> Container:
    return Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )


@pytest.fixture
def health_reporter_service(container: Container) -> HealthReporterService:
    return container.resolve(HealthReporterService)


@pytest.fixture
def check_health_use_case(container: Container) -> CheckHealthUseCase:
    return container.resolve(CheckHealthUseCase)
