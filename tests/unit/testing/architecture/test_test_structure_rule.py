from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)

INTERNAL_COLLABORATOR_MOCK_MESSAGE = (
    "mocks internal use case, service, or capability in integration tests; use the real app graph"
)


def test_tests_mirror_source_structure_rule_accepts_flat_mirrored_tests(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py",
        "class TitleService:\n"
        "    def normalize(self, *, title: str) -> str:\n"
        "        return title.strip()\n",
    )
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "test_title_service.py",
        "def test_title_service() -> None:\n    assert True\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "tasks.py",
        "class TasksController:\n    pass\n",
    )
    _write(
        tmp_path
        / "tests"
        / "integration"
        / "delivery"
        / "fastapi"
        / "controllers"
        / "test_tasks.py",
        "def test_tasks_controller() -> None:\n    assert True\n",
    )
    _write(
        tmp_path
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "infrastructure"
        / "sqlalchemy"
        / "repositories"
        / "task_repository.py",
        "class SQLAlchemyTaskRepository:\n    pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "infrastructure" / "sqlalchemy" / "session.py",
        "class SQLAlchemySessionFactory:\n    pass\n",
    )
    _write(
        tmp_path / "src" / "demo_service" / "ioc" / "container.py",
        "def get_container() -> object:\n    return object()\n",
    )
    _write(
        tmp_path / "tests" / "integration" / "migrations" / "test_alembic.py",
        "def test_alembic() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert report.violations == ()


def test_tests_mirror_source_structure_rule_accepts_nested_flat_core_tests(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path
        / "src"
        / "demo_service"
        / "core"
        / "tasks"
        / "use_cases"
        / "admin"
        / "create_task.py",
        "class CreateTaskUseCase:\n    pass\n",
    )
    _write(
        tmp_path
        / "tests"
        / "unit"
        / "core"
        / "tasks"
        / "use_cases"
        / "admin"
        / "test_create_task.py",
        "def test_create_task() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert report.violations == ()


def test_tests_mirror_source_structure_rule_rejects_target_folder_test(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py",
        "class TitleService:\n    pass\n",
    )
    _write(
        tmp_path
        / "tests"
        / "unit"
        / "core"
        / "tasks"
        / "services"
        / "title_service"
        / "test_title_service.py",
        "def test_title_service() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "core behavior test must be flat; expected "
            "tests/unit/core/tasks/services/test_title_service.py",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_harness_file(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "harness.py",
        "class TitleServiceHarness:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "harness.py is not allowed; resolve targets directly from the container in flat "
            "test modules",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_orphan_test_path(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "test_missing_service.py",
        "def test_missing_service() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test does not mirror a source module; expected "
            "src/demo_service/core/tasks/services/missing_service.py",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_generic_scenarios_file(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "_scenarios.py",
        "VALUE = 1\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "generic scenario files are not allowed; keep setup in the test module that uses it",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_closure_style_use_fixture(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "conftest.py",
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def use_short_codes():\n"
        "    def use_code(code: str) -> str:\n"
        "        return code\n\n"
        "    return use_code\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "closure-style use_* fixture factories are not allowed; register overrides directly "
            "before container.resolve(...)",
            "use_short_codes",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_fake_classes_in_support_fakes(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "_support" / "fakes" / "core" / "urls.py",
        "class InMemoryShortUrlRepository:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "tests/_support/fakes is not allowed; keep one-off doubles in test modules and "
            "reused unit doubles in mirrored fake_<source_module>.py modules",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_support_fakes_package(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "_support" / "fakes" / "__init__.py",
        "",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "tests/_support/fakes is not allowed; keep one-off doubles in test modules and "
            "reused unit doubles in mirrored fake_<source_module>.py modules",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_shared_fakes_file(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "_fakes.py",
        "class InMemoryTaskRepository:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "shared _fakes.py files are not allowed; use mirrored fake_<source_module>.py "
            "modules for reused unit doubles",
        )
    ]


def test_tests_mirror_source_structure_rule_accepts_mirrored_fake_modules(
    tmp_path: Path,
) -> None:
    fake_modules = (
        ("capabilities", "short_code_capability", "ShortCodeCapability"),
        ("gateways", "readiness_check_gateway", "ReadinessCheckGateway"),
        ("repositories", "task_repository", "TaskRepository"),
    )
    for package_name, module_name, source_class_name in fake_modules:
        _write(
            tmp_path
            / "src"
            / "demo_service"
            / "core"
            / "tasks"
            / package_name
            / f"{module_name}.py",
            f"class {source_class_name}:\n    pass\n",
        )
        _write(
            tmp_path
            / "tests"
            / "unit"
            / "core"
            / "tasks"
            / package_name
            / f"fake_{module_name}.py",
            "class ReusedDouble:\n    pass\n",
        )
    _write(
        tmp_path
        / "tests"
        / "unit"
        / "core"
        / "tasks"
        / "capabilities"
        / "test_short_code_capability.py",
        "def test_short_code_capability() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert report.violations == ()


def test_tests_mirror_source_structure_rule_rejects_fake_modules_outside_unit_core(
    tmp_path: Path,
) -> None:
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
        tmp_path
        / "tests"
        / "integration"
        / "core"
        / "tasks"
        / "repositories"
        / "fake_task_repository.py",
        "class InMemoryTaskRepository:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "fake_*.py modules are allowed only under tests/unit/core capabilities, gateways, "
            "or repositories packages and must mirror a source module",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_fake_service_modules(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py",
        "class TitleService:\n    pass\n",
    )
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "fake_title_service.py",
        "class FakeTitleService:\n    pass\n",
    )
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "test_title_service.py",
        "def test_title_service() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "fake_*.py modules are allowed only under tests/unit/core capabilities, gateways, "
            "or repositories packages and must mirror a source module",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_fake_modules_without_source(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path
        / "tests"
        / "unit"
        / "core"
        / "tasks"
        / "repositories"
        / "fake_missing_repository.py",
        "class InMemoryMissingRepository:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test does not mirror a source module; expected "
            "src/demo_service/core/tasks/repositories/missing_repository.py",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_double_classes_in_conftest(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "conftest.py",
        "class InMemoryTaskRepository:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test double classes do not belong in conftest.py; define them in the test module "
            "that uses them",
            "InMemoryTaskRepository",
        )
    ]


def test_tests_mirror_source_structure_rule_rejects_behavior_named_doubles_in_conftest(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "conftest.py",
        "\n".join(
            (
                "class SequencedShortCodeCapability:",
                "    pass",
                "",
                "class FixedTaxRateCapability:",
                "    pass",
                "",
                "class TrackingTaskUnitOfWorkManager:",
                "    pass",
            )
        ),
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test double classes do not belong in conftest.py; define them in the test module "
            "that uses them",
            "SequencedShortCodeCapability",
        ),
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test double classes do not belong in conftest.py; define them in the test module "
            "that uses them",
            "FixedTaxRateCapability",
        ),
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "test double classes do not belong in conftest.py; define them in the test module "
            "that uses them",
            "TrackingTaskUnitOfWorkManager",
        ),
    ]


def test_tests_mirror_source_structure_rule_accepts_inline_test_doubles_and_mocks(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py",
        "class TitleService:\n    pass\n",
    )
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "services" / "test_title_service.py",
        "from unittest.mock import MagicMock\n\n"
        "class InMemoryTaskRepository:\n"
        "    pass\n\n"
        "def test_title_service(container) -> None:\n"
        "    repository = InMemoryTaskRepository()\n"
        "    dependency = MagicMock()\n"
        "    container.add_instance(repository, provides=InMemoryTaskRepository)\n"
        "    container.add_instance(dependency, provides=object)\n"
        "    assert repository is not None\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert report.violations == ()


def test_tests_mirror_source_structure_rule_requires_core_behavior_tests(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py",
        "class TitleService:\n"
        "    def normalize(self, *, title: str) -> str:\n"
        "        return title.strip()\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "missing unit test tests/unit/core/tasks/services/test_title_service.py",
        )
    ]


def test_tests_mirror_source_structure_rule_requires_integration_tests_for_uow_use_cases(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "use_cases" / "create_task.py",
        "from diwire import Injected\n"
        "from specx.core.foundation.use_case import BaseUseCase\n\n"
        "class TaskUnitOfWorkManager:\n"
        "    pass\n\n"
        "class CreateTaskUseCase(BaseUseCase):\n"
        "    _unit_of_work_manager: Injected[TaskUnitOfWorkManager]\n",
    )
    _write(
        tmp_path / "tests" / "unit" / "core" / "tasks" / "use_cases" / "test_create_task.py",
        "def test_create_task() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE,
            "missing integration test tests/integration/core/tasks/use_cases/test_create_task.py",
        )
    ]


def test_test_fixtures_do_not_bundle_mocks_rule_rejects_grouped_mock_fixture(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "conftest.py",
        "from unittest.mock import AsyncMock, MagicMock\n"
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def task_use_case_mocks(container):\n"
        "    create_task = MagicMock()\n"
        "    create_task.execute = AsyncMock()\n"
        "    get_task = MagicMock()\n"
        "    get_task.execute = AsyncMock()\n"
        "    container.add_instance(create_task, provides=object)\n"
        "    container.add_instance(get_task, provides=str)\n"
        "    return {object: create_task, str: get_task}\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TEST_FIXTURES_DO_NOT_BUNDLE_MOCKS),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.TEST_FIXTURES_DO_NOT_BUNDLE_MOCKS,
            "bundles multiple mocks; use one fixture per collaborator",
            "task_use_case_mocks",
        )
    ]


def test_test_fixtures_do_not_bundle_mocks_rule_accepts_single_mock_fixture(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "conftest.py",
        "from unittest.mock import AsyncMock, MagicMock\n"
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def create_task_use_case_mock(container):\n"
        "    use_case = MagicMock()\n"
        "    use_case.execute = AsyncMock()\n"
        "    container.add_instance(use_case, provides=object)\n"
        "    return use_case\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.TEST_FIXTURES_DO_NOT_BUNDLE_MOCKS),
        )
    )

    assert report.violations == ()


def test_integration_mock_rule_rejects_internal_use_case_mock(tmp_path: Path) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "test_tasks.py",
        "from unittest.mock import AsyncMock, MagicMock\n"
        "from demo_service.core.tasks.use_cases.create_task import CreateTaskUseCase\n\n"
        "def test_tasks(container) -> None:\n"
        "    use_case = MagicMock(spec=CreateTaskUseCase)\n"
        "    use_case.execute = AsyncMock()\n"
        "    container.add_instance(use_case, provides=CreateTaskUseCase)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS,
            INTERNAL_COLLABORATOR_MOCK_MESSAGE,
            "test_tasks",
        )
    ]


def test_integration_mock_rule_rejects_internal_capability_mock(tmp_path: Path) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "test_tasks.py",
        "from unittest.mock import MagicMock\n"
        "from demo_service.core.tasks.capabilities.slug_capability import SlugCapability\n\n"
        "def test_tasks() -> None:\n"
        "    MagicMock(spec=SlugCapability)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS,
            INTERNAL_COLLABORATOR_MOCK_MESSAGE,
            "test_tasks",
        )
    ]


def test_integration_mock_rule_rejects_monkeypatch_string_target(tmp_path: Path) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "test_tasks.py",
        "def test_tasks(monkeypatch) -> None:\n"
        "    monkeypatch.setattr(\n"
        "        'demo_service.core.tasks.services.title_service.TitleService.normalize',\n"
        "        lambda self, title: title,\n"
        "    )\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS,
            INTERNAL_COLLABORATOR_MOCK_MESSAGE,
            "test_tasks",
        )
    ]


def test_integration_mock_rule_accepts_external_vendor_mock(tmp_path: Path) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "test_tasks.py",
        "from unittest.mock import MagicMock\n"
        "from vendor.core.email import EmailClient\n\n"
        "def test_tasks() -> None:\n"
        "    MagicMock(spec=EmailClient)\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS
            ),
        )
    )

    assert report.violations == ()


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
