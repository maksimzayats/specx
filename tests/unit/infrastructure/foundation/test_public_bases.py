from __future__ import annotations

import pytest

from specx.infrastructure.foundation.settings import BaseRuntimeSettings
from specx.infrastructure.foundation.sqlalchemy.model import BaseSQLAlchemyModel


class ExampleSettings(BaseRuntimeSettings):
    """Settings fixture used to verify runtime settings imports."""

    database_url: str = "sqlite+aiosqlite:///./app.sqlite3"


class RequiredExampleSettings(BaseRuntimeSettings):
    """Settings fixture with a value supplied only at runtime."""

    required_value: str


def test_runtime_settings_base_is_importable() -> None:
    settings = ExampleSettings()

    assert settings.database_url.startswith("sqlite")


def test_runtime_settings_base_loads_required_field_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REQUIRED_VALUE", "from-environment")

    settings = RequiredExampleSettings.from_environment()

    assert settings.required_value == "from-environment"


def test_sqlalchemy_base_keeps_compatibility_metadata_naming_conventions() -> None:
    convention = BaseSQLAlchemyModel.metadata.naming_convention

    assert convention.get("pk") == "pk_%(table_name)s"
    assert convention.get("fk") == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
