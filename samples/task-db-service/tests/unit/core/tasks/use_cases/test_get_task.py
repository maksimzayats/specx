import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.use_cases.get_task import GetTaskQuery, GetTaskUseCase
from tests._support.fakes.core.tasks import InMemoryTaskRepository, InMemoryTaskUnitOfWorkManager


@pytest.mark.anyio
async def test_execute_gets_task_inside_one_unit_of_work_scope(
    get_task_use_case: GetTaskUseCase,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    task = task_repository.add_existing(title="Ship skill")

    result = await get_task_use_case.execute(query=GetTaskQuery(task_id=task.id))

    assert result.id == task.id
    assert result.title == "Ship skill"
    assert task_unit_of_work_manager.entered_count == 1


@pytest.mark.anyio
async def test_execute_rolls_back_when_task_is_missing(
    get_task_use_case: GetTaskUseCase,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    with pytest.raises(TaskNotFoundError):
        await get_task_use_case.execute(query=GetTaskQuery(task_id=404))

    assert task_unit_of_work_manager.rolled_back_count == 1
