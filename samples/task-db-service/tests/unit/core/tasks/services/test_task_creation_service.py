import pytest

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork
from task_db_service.core.tasks.services.task_creation_service import TaskCreationService
from tests._support.fakes.core.tasks import InMemoryTaskRepository


@pytest.mark.anyio
async def test_create_normalizes_and_persists_task(
    task_creation_service: TaskCreationService,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    result = await task_creation_service.create(
        unit_of_work=task_unit_of_work,
        title="  Ship   skill  ",
    )

    assert result.title == "Ship skill"
    assert result.is_completed is False
    assert [task.title for task in await task_repository.list()] == ["Ship skill"]


@pytest.mark.anyio
async def test_create_rejects_blank_title(
    task_creation_service: TaskCreationService,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    with pytest.raises(InvalidTaskTitleValueError):
        await task_creation_service.create(
            unit_of_work=task_unit_of_work,
            title="   ",
        )
