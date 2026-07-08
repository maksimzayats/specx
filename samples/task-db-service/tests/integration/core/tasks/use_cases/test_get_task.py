import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskQuery, GetTaskUseCase


@pytest.mark.anyio
async def test_execute_returns_persisted_task(
    create_task_use_case: CreateTaskUseCase,
    get_task_use_case: GetTaskUseCase,
) -> None:
    created_task = await create_task_use_case.execute(command=CreateTaskCommand(title="Ship skill"))

    loaded_task = await get_task_use_case.execute(query=GetTaskQuery(task_id=created_task.id))

    assert loaded_task == created_task


@pytest.mark.anyio
async def test_execute_raises_when_task_is_missing(
    get_task_use_case: GetTaskUseCase,
) -> None:
    with pytest.raises(TaskNotFoundError):
        await get_task_use_case.execute(query=GetTaskQuery(task_id=404))
