from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_alembic_env_uses_package_model_discovery() -> None:
    text = (PROJECT_ROOT / "migrations" / "env.py").read_text(encoding="utf-8")

    assert "load_sqlalchemy_model_modules(core_package=core_package)" in text
    assert ".infrastructure.sqlalchemy.models." not in text


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
