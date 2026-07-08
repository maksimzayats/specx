from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.infrastructure.sqlalchemy.task_unit_of_work import (
    SQLAlchemyTaskUnitOfWorkManager,
)
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)
from task_db_service.core.tasks.use_cases.complete_task import (
    CompleteTaskCommand,
    CompleteTaskUseCase,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskQuery, GetTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksQuery, ListTasksUseCase
from task_db_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from task_db_service.infrastructure.sqlalchemy.settings import DatabaseSettings


def _unit_of_work_manager(*, database_url: str) -> SQLAlchemyTaskUnitOfWorkManager:
    return SQLAlchemyTaskUnitOfWorkManager(
        _session_factory=SQLAlchemySessionFactory(
            _settings=DatabaseSettings(database_url=database_url),
        ),
    )


@pytest.fixture
def migrated_database_url(
    alembic_config: Config,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> str:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'tasks.sqlite3'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(alembic_config, "head")
    return database_url


@pytest.mark.anyio
async def test_sqlalchemy_task_use_cases_persist_tasks(migrated_database_url: str) -> None:
    unit_of_work_manager = _unit_of_work_manager(database_url=migrated_database_url)
    create_task = CreateTaskUseCase(
        _task_title_normalizer_service=TaskTitleNormalizerService(),
        _unit_of_work_manager=unit_of_work_manager,
    )
    get_task = GetTaskUseCase(_unit_of_work_manager=unit_of_work_manager)
    list_tasks = ListTasksUseCase(_unit_of_work_manager=unit_of_work_manager)
    complete_task = CompleteTaskUseCase(_unit_of_work_manager=unit_of_work_manager)

    created = await create_task.execute(command=CreateTaskCommand(title="  Ship skill  "))
    listed = await list_tasks.execute(query=ListTasksQuery())
    completed = await complete_task.execute(command=CompleteTaskCommand(task_id=created.id))
    loaded = await get_task.execute(query=GetTaskQuery(task_id=created.id))

    assert created.title == "Ship skill"
    assert [task.id for task in listed.tasks] == [created.id]
    assert completed.is_completed is True
    assert loaded.is_completed is True


@pytest.mark.anyio
async def test_sqlalchemy_task_unit_of_work_manager_rolls_back_on_exception(
    migrated_database_url: str,
) -> None:
    unit_of_work_manager = _unit_of_work_manager(database_url=migrated_database_url)

    async def add_then_fail() -> None:
        async with unit_of_work_manager as unit_of_work:
            await unit_of_work.tasks.add(title="rolled back")
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await add_then_fail()

    list_tasks = ListTasksUseCase(_unit_of_work_manager=unit_of_work_manager)
    result = await list_tasks.execute(query=ListTasksQuery())

    assert result.tasks == []


@pytest.mark.anyio
async def test_sqlalchemy_task_unit_of_work_manager_rejects_nested_scopes(
    migrated_database_url: str,
) -> None:
    unit_of_work_manager = _unit_of_work_manager(database_url=migrated_database_url)

    async with unit_of_work_manager:
        with pytest.raises(RuntimeError, match="Nested task unit of work"):
            async with unit_of_work_manager:
                raise AssertionError("nested scope should not open")


@pytest.mark.anyio
async def test_get_task_raises_when_missing(migrated_database_url: str) -> None:
    get_task = GetTaskUseCase(
        _unit_of_work_manager=_unit_of_work_manager(database_url=migrated_database_url),
    )

    with pytest.raises(TaskNotFoundError):
        await get_task.execute(query=GetTaskQuery(task_id=404))
