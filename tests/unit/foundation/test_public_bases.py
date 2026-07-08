from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass

import pytest

from specx.foundation.command import BaseCommand
from specx.foundation.delivery.fastapi.schema import BaseFastAPISchema
from specx.foundation.dto import BaseDTO
from specx.foundation.enums import BaseStrEnum
from specx.foundation.exceptions import BaseApplicationError, BaseApplicationValueError
from specx.foundation.infrastructure.sqlalchemy.model import BaseSQLAlchemyModel
from specx.foundation.query import BaseQuery
from specx.foundation.settings import BaseRuntimeSettings


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleDTO(BaseDTO):
    """DTO fixture used to verify the public Specx foundation base."""

    name: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleCommand(BaseCommand):
    """Command fixture used to verify command inheritance."""

    title: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleQuery(BaseQuery):
    """Query fixture used to verify query inheritance."""

    id: int


class ExampleSchema(BaseFastAPISchema):
    """Schema fixture used to verify delivery schema validation."""

    id: int


class ExampleSettings(BaseRuntimeSettings):
    """Settings fixture used to verify runtime settings imports."""

    database_url: str = "sqlite+aiosqlite:///./app.sqlite3"


class ExampleEnum(BaseStrEnum):
    """Enum fixture used to verify public string enum behavior."""

    LOCAL = "local"


def mutate_attribute(target: object, *, name: str, value: object) -> None:
    setattr(target, name, value)


def test_core_data_foundation_bases_support_dataclass_contracts() -> None:
    dto = ExampleDTO(name="Ship")
    command = ExampleCommand(title="Write docs")
    query = ExampleQuery(id=1)

    assert is_dataclass(dto)
    assert is_dataclass(command)
    assert is_dataclass(query)
    assert dto.name == "Ship"
    assert command.title == "Write docs"
    assert query.id == 1
    assert not hasattr(dto, "__dict__")

    with pytest.raises(FrozenInstanceError):
        mutate_attribute(dto, name="name", value="Changed")


def test_delivery_schema_base_still_supports_pydantic_validation() -> None:
    schema = ExampleSchema.model_validate({"id": 1})

    assert schema.id == 1


def test_runtime_foundation_bases_are_importable() -> None:
    settings = ExampleSettings()

    assert settings.database_url.startswith("sqlite")
    assert ExampleEnum.LOCAL.value == "local"
    assert issubclass(BaseApplicationError, Exception)
    assert issubclass(BaseApplicationValueError, ValueError)


def test_sqlalchemy_base_owns_metadata_naming_conventions() -> None:
    convention = BaseSQLAlchemyModel.metadata.naming_convention

    assert convention.get("pk") == "pk_%(table_name)s"
    assert convention.get("fk") == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
