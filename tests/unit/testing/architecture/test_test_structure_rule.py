from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_tests_mirror_source_structure_rule_accepts_mirrored_tests(tmp_path: Path) -> None:
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


def test_integration_tests_do_not_mock_internal_use_cases_or_services_rule_rejects_use_case_mock(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "conftest.py",
        "from unittest.mock import AsyncMock, MagicMock\n"
        "import pytest\n"
        "from demo_service.core.tasks.use_cases.create_task import CreateTaskUseCase\n\n"
        "@pytest.fixture\n"
        "def create_task_use_case_mock(container):\n"
        "    use_case = MagicMock(spec=CreateTaskUseCase)\n"
        "    use_case.execute = AsyncMock()\n"
        "    container.add_instance(use_case, provides=CreateTaskUseCase)\n"
        "    return use_case\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_USE_CASES_OR_SERVICES
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_USE_CASES_OR_SERVICES,
            "mocks internal use case/service in integration tests; use the real app graph",
            "create_task_use_case_mock",
        )
    ]


def test_integration_tests_do_not_mock_internal_use_cases_or_services_rule_accepts_external_mock(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tests" / "integration" / "delivery" / "fastapi" / "conftest.py",
        "from unittest.mock import MagicMock\n"
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def openai_client_mock():\n"
        "    return MagicMock()\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_USE_CASES_OR_SERVICES
            ),
        )
    )

    assert report.violations == ()


def test_init_files_are_empty_rule_rejects_missing_test_package_init(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "src" / "demo_service" / "__init__.py", "")
    _write(tmp_path / "tests" / "__init__.py", "")
    _write(tmp_path / "tests" / "unit" / "__init__.py", "")
    _write(
        tmp_path / "tests" / "unit" / "core" / "test_title.py",
        "def test_title() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.INIT_FILES_ARE_EMPTY),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.INIT_FILES_ARE_EMPTY,
            "__init__.py is missing",
        )
    ]


def test_init_files_are_empty_rule_rejects_non_empty_test_package_init(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "src" / "demo_service" / "__init__.py", "")
    _write(tmp_path / "tests" / "__init__.py", "")
    _write(tmp_path / "tests" / "unit" / "__init__.py", "VALUE = 1\n")
    _write(
        tmp_path / "tests" / "unit" / "test_title.py",
        "def test_title() -> None:\n    assert True\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.INIT_FILES_ARE_EMPTY),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.INIT_FILES_ARE_EMPTY,
            "__init__.py is not empty",
        )
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
