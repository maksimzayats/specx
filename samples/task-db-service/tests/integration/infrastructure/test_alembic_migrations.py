from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

import task_db_service.core as core_package
from task_db_service.foundation.infrastructure.sqlalchemy.model import BaseSQLAlchemyModel
from task_db_service.infrastructure.sqlalchemy import model_discovery
from task_db_service.infrastructure.sqlalchemy.model_discovery import (
    iter_sqlalchemy_model_module_names,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src" / "task_db_service"


def _model_module_names_from_files() -> set[str]:
    return {
        "task_db_service." + ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)
        for path in (SRC_ROOT / "core").glob("*/infrastructure/sqlalchemy/models/*.py")
        if path.name != "__init__.py"
    }


def _model_table_names_from_modules(module_names: set[str]) -> set[str]:
    table_names: set[str] = set()
    for module_name in module_names:
        module = import_module(module_name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseSQLAlchemyModel)
                and value is not BaseSQLAlchemyModel
            ):
                table_name = getattr(value, "__tablename__", None)
                if isinstance(table_name, str):
                    table_names.add(table_name)
    return table_names


def test_alembic_env_uses_package_model_discovery() -> None:
    text = (PROJECT_ROOT / "migrations" / "env.py").read_text(encoding="utf-8")

    assert "load_sqlalchemy_model_modules(core_package=core_package)" in text
    assert ".infrastructure.sqlalchemy.models." not in text


def test_alembic_model_discovery_finds_every_core_model_module() -> None:
    discovered_module_names = set(
        iter_sqlalchemy_model_module_names(core_package=core_package),
    )

    assert discovered_module_names == _model_module_names_from_files()


def test_alembic_model_loader_imports_every_discovered_model_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported_module_names: list[str] = []

    def fake_import_module(module_name: str) -> ModuleType:
        imported_module_names.append(module_name)
        return ModuleType(module_name)

    monkeypatch.setattr(model_discovery, "import_module", fake_import_module)

    model_discovery.load_sqlalchemy_model_modules(core_package=core_package)

    assert set(imported_module_names) == _model_module_names_from_files()


def test_alembic_model_discovery_loads_model_tables_into_metadata() -> None:
    expected_table_names = _model_table_names_from_modules(_model_module_names_from_files())

    model_discovery.load_sqlalchemy_model_modules(core_package=core_package)

    assert expected_table_names <= set(BaseSQLAlchemyModel.metadata.tables)


def test_alembic_migrations_create_schema(
    alembic_config: Config,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")

    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        inspector = inspect(engine)
        assert sorted(inspector.get_table_names()) == ["alembic_version", "tasks"]
        columns = {column["name"] for column in inspector.get_columns("tasks")}
        assert columns == {"id", "title", "is_completed"}
    finally:
        engine.dispose()


def test_alembic_migrations_match_models(
    alembic_config: Config,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "drift.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")

    command.upgrade(alembic_config, "head")
    command.check(alembic_config)
