import pytest

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksQuery, ListTasksUseCase


@pytest.mark.anyio
async def test_execute_normalizes_and_persists_task(
    create_task_use_case: CreateTaskUseCase,
    list_tasks_use_case: ListTasksUseCase,
) -> None:
    created_task = await create_task_use_case.execute(
        command=CreateTaskCommand(title="  Ship skill  "),
    )
    listed_tasks = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert created_task.title == "Ship skill"
    assert listed_tasks.tasks == [created_task]


@pytest.mark.anyio
async def test_execute_rejects_blank_title_without_persisting_task(
    create_task_use_case: CreateTaskUseCase,
    list_tasks_use_case: ListTasksUseCase,
) -> None:
    with pytest.raises(InvalidTaskTitleValueError):
        await create_task_use_case.execute(command=CreateTaskCommand(title="   "))

    listed_tasks = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert listed_tasks.tasks == []
