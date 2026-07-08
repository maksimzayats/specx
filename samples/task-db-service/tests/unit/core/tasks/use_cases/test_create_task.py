import pytest

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from tests._support.fakes.core.tasks import InMemoryTaskRepository, InMemoryTaskUnitOfWorkManager


@pytest.mark.anyio
async def test_execute_creates_task_inside_one_unit_of_work_scope(
    create_task_use_case: CreateTaskUseCase,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    result = await create_task_use_case.execute(command=CreateTaskCommand(title="  Ship skill  "))

    assert result.title == "Ship skill"
    assert task_unit_of_work_manager.entered_count == 1
    assert task_unit_of_work_manager.committed_count == 1


@pytest.mark.anyio
async def test_execute_rolls_back_when_title_is_invalid(
    create_task_use_case: CreateTaskUseCase,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work_manager: InMemoryTaskUnitOfWorkManager,
) -> None:
    with pytest.raises(InvalidTaskTitleValueError):
        await create_task_use_case.execute(command=CreateTaskCommand(title="   "))

    assert await task_repository.list() == []
    assert task_unit_of_work_manager.rolled_back_count == 1
