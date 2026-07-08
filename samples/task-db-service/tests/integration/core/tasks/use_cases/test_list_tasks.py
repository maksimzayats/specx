import pytest

from task_db_service.core.tasks.use_cases.complete_task import (
    CompleteTaskCommand,
    CompleteTaskUseCase,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksQuery, ListTasksUseCase


@pytest.mark.anyio
async def test_execute_returns_persisted_tasks_in_creation_order(
    create_task_use_case: CreateTaskUseCase,
    complete_task_use_case: CompleteTaskUseCase,
    list_tasks_use_case: ListTasksUseCase,
) -> None:
    first_task = await create_task_use_case.execute(command=CreateTaskCommand(title="First"))
    second_task = await create_task_use_case.execute(command=CreateTaskCommand(title="Second"))
    completed_second_task = await complete_task_use_case.execute(
        command=CompleteTaskCommand(task_id=second_task.id),
    )

    listed_tasks = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert listed_tasks.tasks == [first_task, completed_second_task]
