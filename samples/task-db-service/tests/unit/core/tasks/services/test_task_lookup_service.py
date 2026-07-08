import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork
from task_db_service.core.tasks.services.task_lookup_service import TaskLookupService
from tests._support.fakes.core.tasks import InMemoryTaskRepository


@pytest.mark.anyio
async def test_get_returns_task_dto(
    task_lookup_service: TaskLookupService,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    task = task_repository.add_existing(title="Ship skill")

    result = await task_lookup_service.get(
        unit_of_work=task_unit_of_work,
        task_id=task.id,
    )

    assert result.id == task.id
    assert result.title == "Ship skill"
    assert result.is_completed is False


@pytest.mark.anyio
async def test_get_raises_when_task_is_missing(
    task_lookup_service: TaskLookupService,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    with pytest.raises(TaskNotFoundError) as error:
        await task_lookup_service.get(
            unit_of_work=task_unit_of_work,
            task_id=404,
        )

    assert error.value.task_id == 404


@pytest.mark.anyio
async def test_list_returns_tasks_in_repository_order(
    task_lookup_service: TaskLookupService,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    task_repository.add_existing(title="First")
    task_repository.add_existing(title="Second", is_completed=True)

    result = await task_lookup_service.list(unit_of_work=task_unit_of_work)

    assert [(task.title, task.is_completed) for task in result.tasks] == [
        ("First", False),
        ("Second", True),
    ]
