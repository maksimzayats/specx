from __future__ import annotations

import pytest
from diwire import Container

from task_db_service.core.tasks.use_cases.complete_task import CompleteTaskUseCase
from task_db_service.core.tasks.use_cases.create_task import CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksUseCase


@pytest.fixture
def create_task_use_case(transactional_container: Container) -> CreateTaskUseCase:
    return transactional_container.resolve(CreateTaskUseCase)


@pytest.fixture
def get_task_use_case(transactional_container: Container) -> GetTaskUseCase:
    return transactional_container.resolve(GetTaskUseCase)


@pytest.fixture
def list_tasks_use_case(transactional_container: Container) -> ListTasksUseCase:
    return transactional_container.resolve(ListTasksUseCase)


@pytest.fixture
def complete_task_use_case(transactional_container: Container) -> CompleteTaskUseCase:
    return transactional_container.resolve(CompleteTaskUseCase)
