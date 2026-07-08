import pytest

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWork
from task_db_service.core.tasks.services.task_completion_service import TaskCompletionService
from tests._support.fakes.core.tasks import InMemoryTaskRepository


@pytest.mark.anyio
async def test_complete_marks_task_complete(
    task_completion_service: TaskCompletionService,
    task_repository: InMemoryTaskRepository,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    task = task_repository.add_existing(title="Ship skill")

    result = await task_completion_service.complete(
        unit_of_work=task_unit_of_work,
        task_id=task.id,
    )

    assert result.id == task.id
    assert result.is_completed is True


@pytest.mark.anyio
async def test_complete_raises_when_task_is_missing(
    task_completion_service: TaskCompletionService,
    task_unit_of_work: TaskUnitOfWork,
) -> None:
    with pytest.raises(TaskNotFoundError) as error:
        await task_completion_service.complete(
            unit_of_work=task_unit_of_work,
            task_id=404,
        )

    assert error.value.task_id == 404
