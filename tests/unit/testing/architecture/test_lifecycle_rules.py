from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_suffix_rule_accepts_base_lifecycle_category(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "lifecycle.py",
        "from specx.delivery.foundation.lifecycle import BaseLifecycle\n\n"
        "class FastAPILifecycle(BaseLifecycle[object]):\n"
        "    def __call__(self, app: object):\n"
        "        raise NotImplementedError\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.CLASSES_USE_SUFFIX_FROM_MOST_SPECIFIC_FOUNDATION_CATEGORY
            ),
        )
    )

    assert report.violations == ()


def test_container_rule_allows_fastapi_lifecycle_to_inject_container(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "lifecycle.py",
        "from contextlib import asynccontextmanager\n"
        "from dataclasses import dataclass\n"
        "from typing import AsyncIterator\n\n"
        "from diwire import Container, Injected\n"
        "from specx.delivery.foundation.lifecycle import BaseLifecycle\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class FastAPILifecycle(BaseLifecycle[object]):\n"
        "    _container: Injected[Container]\n\n"
        "    @asynccontextmanager\n"
        "    async def __call__(self, app: object) -> AsyncIterator[None]:\n"
        "        yield\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.ONLY_IOC_DELIVERY_APP_AND_TESTS_IMPORT_CONTAINER
            ),
        )
    )

    assert report.violations == ()


def test_container_rule_allows_framework_neutral_delivery_lifecycle(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "starlette" / "lifecycle.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n"
        "from specx.delivery.foundation.lifecycle import BaseLifecycle\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class StarletteLifecycle(BaseLifecycle[object]):\n"
        "    _container: Injected[Container]\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.ONLY_IOC_DELIVERY_APP_AND_TESTS_IMPORT_CONTAINER
            ),
        )
    )

    assert report.violations == ()


def test_container_rule_rejects_container_injection_outside_fastapi_lifecycle_class(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "factory.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n"
        "from specx.core.foundation.factory import BaseFactory\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class FastAPIFactory(BaseFactory):\n"
        "    def __init__(self, container: Injected[Container]) -> None:\n"
        "        self._container = container\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "lifecycle.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class LifecycleContainerCloser:\n"
        "    def __init__(self, container: Injected[Container]) -> None:\n"
        "        self._container = container\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "tasks.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n"
        "from specx.delivery.foundation.controller import BaseController\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class TasksController(BaseController[object]):\n"
        "    _container: Injected[Container]\n\n"
        "    def register(self, registry: object) -> None:\n"
        "        pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _container: Injected[Container]\n",
    )
    _write(
        tmp_path
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "infrastructure"
        / "sqlalchemy"
        / "task_gateway.py",
        "from dataclasses import dataclass\n\n"
        "from diwire import Container, Injected\n"
        "from specx.core.foundation.gateway import BaseGateway\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class SQLAlchemyTaskGateway(BaseGateway):\n"
        "    _container: Injected[Container]\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.ONLY_IOC_DELIVERY_APP_AND_TESTS_IMPORT_CONTAINER
            ),
        )
    )

    injection_violations = {
        violation.symbol
        for violation in report.violations
        if violation.message == "injects diwire.Container outside delivery lifecycle"
    }

    assert injection_violations == {
        "CreateTaskUseCase",
        "FastAPIFactory",
        "LifecycleContainerCloser",
        "SQLAlchemyTaskGateway",
        "TasksController",
    }


def test_delivery_boundary_rule_allows_top_level_infrastructure_in_lifecycle(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "infrastructure" / "sqlalchemy" / "session.py",
        "class SQLAlchemySessionFactory:\n    pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "lifecycle.py",
        "from demo_service.infrastructure.sqlalchemy.session import "
        "SQLAlchemySessionFactory\n\n"
        "class FastAPILifecycle:\n"
        "    _session_factory: SQLAlchemySessionFactory\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.DELIVERY_CONTROLLERS_DO_NOT_IMPORT_INFRASTRUCTURE
            ),
        )
    )

    assert report.violations == ()


def test_delivery_boundary_rule_rejects_scope_technical_imports_in_app_modules(
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
        tmp_path
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "repositories"
        / "task_repository.py",
        "class TaskRepository:\n    pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "lifecycle.py",
        "from demo_service.core.tasks.infrastructure.sqlalchemy.task_repository import "
        "SQLAlchemyTaskRepository\n"
        "from demo_service.core.tasks.repositories.task_repository import TaskRepository\n\n"
        "class FastAPILifecycle:\n"
        "    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.DELIVERY_CONTROLLERS_DO_NOT_IMPORT_INFRASTRUCTURE
            ),
        )
    )

    assert {violation.message for violation in report.violations} == {
        "imports demo_service.core.tasks.infrastructure.sqlalchemy.task_repository",
        "imports demo_service.core.tasks.repositories.task_repository",
    }


def test_delivery_boundary_rule_rejects_scope_technical_imports_in_controllers(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "tasks.py",
        "from demo_service.core.tasks.models.task import TaskModel\n"
        "from demo_service.core.tasks.repositories.task_repository import TaskRepository\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.DELIVERY_CONTROLLERS_DO_NOT_IMPORT_INFRASTRUCTURE
            ),
        )
    )

    assert {violation.message for violation in report.violations} == {
        "imports demo_service.core.tasks.models.task",
        "imports demo_service.core.tasks.repositories.task_repository",
    }


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
