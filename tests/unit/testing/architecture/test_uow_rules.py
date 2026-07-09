from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_accepts_manager_owned_uow(
    tmp_path: Path,
) -> None:
    _write_repository_contract(tmp_path)
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "from demo_service.core.tasks.repositories.task_unit_of_work import "
        "TaskUnitOfWorkManager\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        async with self._unit_of_work_manager as unit_of_work:\n"
        "            task_id = await unit_of_work.tasks.add(title=command.title)\n\n"
        "        return TaskDTO(task_id=task_id)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    assert report.violations == ()


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_rejects_repository_injection(
    tmp_path: Path,
) -> None:
    _write_repository_contract(tmp_path)
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "from demo_service.core.tasks.repositories.task_repository import TaskRepository\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _task_repository: Injected[TaskRepository]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        task_id = await self._task_repository.add(title=command.title)\n\n"
        "        return TaskDTO(task_id=task_id)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "injects ['_task_repository:Injected[TaskRepository]']; "
            "calls repositories outside manager-owned UoW ['self._task_repository.add']",
            "CreateTaskUseCase",
        )
    ]


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_rejects_sqlalchemy_session(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from sqlalchemy.ext.asyncio import AsyncSession\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _session: Injected[AsyncSession]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        _ = command\n"
        "        return TaskDTO(task_id=1)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "imports sqlalchemy.ext.asyncio",
            None,
        ),
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "imports sqlalchemy.ext.asyncio.AsyncSession",
            None,
        ),
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "injects ['_session:Injected[AsyncSession]']",
            "CreateTaskUseCase",
        ),
    ]


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_rejects_infrastructure_import(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "infrastructure"
        / "sqlalchemy"
        / "task_repository.py",
        "class SQLAlchemyTaskRepository:\n    pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "from demo_service.core.tasks.infrastructure.sqlalchemy.task_repository import "
        "SQLAlchemyTaskRepository\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _repository: Injected[SQLAlchemyTaskRepository]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        task_id = await self._repository.add(title=command.title)\n\n"
        "        return TaskDTO(task_id=task_id)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    assert [violation.message for violation in report.violations] == [
        "imports demo_service.core.tasks.infrastructure.sqlalchemy.task_repository",
        "imports demo_service.core.tasks.infrastructure.sqlalchemy.task_repository."
        "SQLAlchemyTaskRepository",
        "injects ['_repository:Injected[SQLAlchemyTaskRepository]']; "
        "calls repositories outside manager-owned UoW ['self._repository.add']",
    ]


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_rejects_repository_aliases(
    tmp_path: Path,
) -> None:
    _write_repository_contract(tmp_path)
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "from demo_service.core.tasks.repositories.task_unit_of_work import "
        "TaskUnitOfWorkManager\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        async with self._unit_of_work_manager as unit_of_work:\n"
        "            tasks = unit_of_work.tasks\n"
        "            task_id = await tasks.add(title=command.title)\n\n"
        "        return TaskDTO(task_id=task_id)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "calls repositories outside manager-owned UoW ['tasks.add']",
            "CreateTaskUseCase",
        )
    ]


def test_use_cases_do_not_inject_repositories_or_infrastructure_rule_rejects_non_manager_uow(
    tmp_path: Path,
) -> None:
    _write_repository_contract(tmp_path)
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.command import BaseCommand\n"
        "from specx.core.foundation.dto import BaseDTO\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class CreateTaskCommand(BaseCommand):\n"
        "    title: str\n\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class TaskDTO(BaseDTO):\n"
        "    task_id: int\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _transaction_boundary: Injected[object]\n\n"
        "    async def execute(self, *, command: CreateTaskCommand) -> TaskDTO:\n"
        "        async with self._transaction_boundary as unit_of_work:\n"
        "            task_id = await unit_of_work.tasks.add(title=command.title)\n\n"
        "        return TaskDTO(task_id=task_id)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE,
            "calls repositories outside manager-owned UoW ['unit_of_work.tasks.add']",
            "CreateTaskUseCase",
        )
    ]


def _write_repository_contract(project_root: Path) -> None:
    _write(
        project_root
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "repositories"
        / "task_repository.py",
        "from specx.core.foundation.repository import BaseRepository\n\n"
        "class TaskRepository(BaseRepository):\n"
        "    async def add(self, *, title: str) -> int:\n"
        "        return 1\n",
    )
    _write(
        project_root
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "repositories"
        / "task_unit_of_work.py",
        "from specx.core.foundation.unit_of_work import BaseUnitOfWork\n"
        "from specx.core.foundation.unit_of_work_manager import BaseUnitOfWorkManager\n\n"
        "from demo_service.core.tasks.repositories.task_repository import TaskRepository\n\n"
        "class TaskUnitOfWork(BaseUnitOfWork):\n"
        "    tasks: TaskRepository\n\n"
        "class TaskUnitOfWorkManager(BaseUnitOfWorkManager[TaskUnitOfWork]):\n"
        "    pass\n",
    )


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
