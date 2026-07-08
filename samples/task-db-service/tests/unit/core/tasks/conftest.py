from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from diwire import Container

from task_db_service.core.tasks.repositories.task_unit_of_work import (
    TaskUnitOfWork,
    TaskUnitOfWorkManager,
)
from task_db_service.core.tasks.services.task_completion_service import TaskCompletionService
from task_db_service.core.tasks.services.task_creation_service import TaskCreationService
from task_db_service.core.tasks.services.task_lookup_service import TaskLookupService
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)
from task_db_service.core.tasks.use_cases.complete_task import CompleteTaskUseCase
from task_db_service.core.tasks.use_cases.create_task import CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksUseCase
from task_db_service.ioc.container import get_container
from tests._support.fakes.core.tasks import (
    InMemoryTaskRepository,
    InMemoryTaskUnitOfWorkManager,
)


@pytest.fixture
def container() -> Container:
    container = get_container()
    repository = InMemoryTaskRepository()
    unit_of_work_manager = InMemoryTaskUnitOfWorkManager(repository=repository)
    container.add_instance(repository, provides=InMemoryTaskRepository)
    container.add_instance(unit_of_work_manager, provides=InMemoryTaskUnitOfWorkManager)
    container.add_instance(unit_of_work_manager, provides=TaskUnitOfWorkManager)
    return container


@pytest.fixture
def task_repository(container: Container) -> InMemoryTaskRepository:
    return container.resolve(InMemoryTaskRepository)


@pytest.fixture
def task_unit_of_work_manager(container: Container) -> InMemoryTaskUnitOfWorkManager:
    return container.resolve(InMemoryTaskUnitOfWorkManager)


@pytest.fixture
async def task_unit_of_work(
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> AsyncIterator[TaskUnitOfWork]:
    async with task_unit_of_work_manager as unit_of_work:
        yield unit_of_work


@pytest.fixture
def task_title_normalizer_service(container: Container) -> TaskTitleNormalizerService:
    return container.resolve(TaskTitleNormalizerService)


@pytest.fixture
def task_creation_service(container: Container) -> TaskCreationService:
    return container.resolve(TaskCreationService)


@pytest.fixture
def task_lookup_service(container: Container) -> TaskLookupService:
    return container.resolve(TaskLookupService)


@pytest.fixture
def task_completion_service(container: Container) -> TaskCompletionService:
    return container.resolve(TaskCompletionService)


@pytest.fixture
def create_task_use_case(container: Container) -> CreateTaskUseCase:
    return container.resolve(CreateTaskUseCase)


@pytest.fixture
def get_task_use_case(container: Container) -> GetTaskUseCase:
    return container.resolve(GetTaskUseCase)


@pytest.fixture
def list_tasks_use_case(container: Container) -> ListTasksUseCase:
    return container.resolve(ListTasksUseCase)


@pytest.fixture
def complete_task_use_case(container: Container) -> CompleteTaskUseCase:
    return container.resolve(CompleteTaskUseCase)
