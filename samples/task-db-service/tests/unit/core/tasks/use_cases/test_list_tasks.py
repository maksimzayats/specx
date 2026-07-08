import pytest

from task_db_service.core.tasks.use_cases.list_tasks import ListTasksQuery, ListTasksUseCase
from tests._support.fakes.core.tasks import InMemoryTaskRepository, InMemoryTaskUnitOfWorkManager


@pytest.mark.anyio
async def test_execute_lists_tasks_inside_one_unit_of_work_scope(
    list_tasks_use_case: ListTasksUseCase,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    task_repository.add_existing(title="First")
    task_repository.add_existing(title="Second", is_completed=True)

    result = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert [(task.title, task.is_completed) for task in result.tasks] == [
        ("First", False),
        ("Second", True),
    ]
    assert task_unit_of_work_manager.entered_count == 1
