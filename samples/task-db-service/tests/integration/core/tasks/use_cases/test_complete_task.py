import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.use_cases.complete_task import (
    CompleteTaskCommand,
    CompleteTaskUseCase,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskQuery, GetTaskUseCase


@pytest.mark.anyio
async def test_execute_persists_completed_state(
    create_task_use_case: CreateTaskUseCase,
    complete_task_use_case: CompleteTaskUseCase,
    get_task_use_case: GetTaskUseCase,
) -> None:
    created_task = await create_task_use_case.execute(command=CreateTaskCommand(title="Ship skill"))

    completed_task = await complete_task_use_case.execute(
        command=CompleteTaskCommand(task_id=created_task.id),
    )
    reloaded_task = await get_task_use_case.execute(query=GetTaskQuery(task_id=created_task.id))

    assert completed_task.id == created_task.id
    assert completed_task.is_completed is True
    assert reloaded_task == completed_task


@pytest.mark.anyio
async def test_execute_raises_when_task_is_missing(
    complete_task_use_case: CompleteTaskUseCase,
) -> None:
    with pytest.raises(TaskNotFoundError):
        await complete_task_use_case.execute(command=CompleteTaskCommand(task_id=404))
