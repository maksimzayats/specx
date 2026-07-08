import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.use_cases.complete_task import (
    CompleteTaskCommand,
    CompleteTaskUseCase,
)
from tests._support.fakes.core.tasks import InMemoryTaskRepository, InMemoryTaskUnitOfWorkManager


@pytest.mark.anyio
async def test_execute_completes_task_inside_one_unit_of_work_scope(
    complete_task_use_case: CompleteTaskUseCase,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    task = task_repository.add_existing(title="Ship skill")

    result = await complete_task_use_case.execute(command=CompleteTaskCommand(task_id=task.id))

    assert result.id == task.id
    assert result.is_completed is True
    assert task_unit_of_work_manager.entered_count == 1


@pytest.mark.anyio
async def test_execute_rolls_back_when_task_is_missing(
    complete_task_use_case: CompleteTaskUseCase,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    with pytest.raises(TaskNotFoundError):
        await complete_task_use_case.execute(command=CompleteTaskCommand(task_id=404))

    assert task_unit_of_work_manager.rolled_back_count == 1
