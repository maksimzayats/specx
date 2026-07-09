from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_logging_rule_accepts_class_local_stdlib_logger(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "import logging\n"
        "from dataclasses import dataclass, field\n\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _logger: logging.Logger = field(init=False, repr=False)\n\n"
        "    def __post_init__(self) -> None:\n"
        "        self._logger = logging.getLogger(\n"
        "            f'{self.__class__.__module__}.{self.__class__.__qualname__}',\n"
        "        )\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS),
        )
    )

    assert report.violations == ()


def test_logging_rule_rejects_injected_logging_logger(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "task_service.py",
        "import logging\n"
        "from dataclasses import dataclass\n\n"
        "from diwire import Injected\n"
        "from specx.core.foundation.effect_service import BaseEffectService\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class TaskService(BaseEffectService):\n"
        "    _logger: Injected[logging.Logger]\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS,
            "injects logger field _logger:Injected[Logger]",
            "TaskService",
        )
    ]


def test_logging_rule_rejects_injected_imported_logger_alias(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "tasks.py",
        "from dataclasses import dataclass\n"
        "from logging import Logger as PythonLogger\n\n"
        "from diwire import Injected\n"
        "from specx.delivery.foundation.controller import BaseController\n\n"
        "@dataclass(kw_only=True, slots=True)\n"
        "class TasksController(BaseController):\n"
        "    _logger: Injected[PythonLogger]\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS,
            "injects logger field _logger:Injected[Logger]",
            "TasksController",
        )
    ]


def test_logging_rule_rejects_logger_container_registration(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "ioc" / "container.py",
        "import logging\n\n"
        "from diwire import Container\n\n"
        "def get_container() -> Container:\n"
        "    container = Container()\n"
        "    container.add_instance(logging.getLogger(__name__), provides=logging.Logger)\n"
        "    return container\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS,
            "registers logging.Logger in the DI container",
            None,
        )
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
