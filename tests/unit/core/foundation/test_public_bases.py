from __future__ import annotations

from abc import abstractmethod
from dataclasses import FrozenInstanceError, dataclass, is_dataclass
from inspect import isabstract
from typing import Any, cast

import pytest

from specx.core.foundation.command import BaseCommand
from specx.core.foundation.dto import BaseDTO
from specx.core.foundation.entity import BaseEntity
from specx.core.foundation.enums import BaseStrEnum
from specx.core.foundation.exceptions import BaseApplicationError, BaseApplicationValueError
from specx.core.foundation.gateway import BaseGateway
from specx.core.foundation.query import BaseQuery
from specx.core.foundation.repository import BaseRepository
from specx.core.foundation.unit_of_work import BaseUnitOfWork
from specx.core.foundation.use_case import BaseUseCase


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleDTO(BaseDTO):
    """DTO fixture used to verify the public specx core foundation base."""

    name: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleCommand(BaseCommand):
    """Command fixture used to verify command inheritance."""

    title: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ExampleQuery(BaseQuery):
    """Query fixture used to verify query inheritance."""

    id: int


class ExampleEnum(BaseStrEnum):
    """Enum fixture used to verify public string enum behavior."""

    LOCAL = "local"


class ExampleGateway(BaseGateway):
    """Gateway fixture used to verify abstract port enforcement."""

    @abstractmethod
    async def send(self) -> None:
        raise NotImplementedError


class ExampleRepository(BaseRepository):
    """Repository fixture used to verify abstract port enforcement."""

    @abstractmethod
    async def get(self) -> object | None:
        raise NotImplementedError


class ExampleUnitOfWork(BaseUnitOfWork):
    """Unit-of-work fixture used to verify abstract contract enforcement."""

    @property
    @abstractmethod
    def records(self) -> ExampleRepository:
        raise NotImplementedError


class ExampleUseCase(BaseUseCase):
    """Use-case fixture used to verify use cases do not force one signature."""


def mutate_attribute(target: object, *, name: str, value: object) -> None:
    setattr(target, name, value)


def instantiate_abstract(target: object) -> object:
    return cast(Any, target)()


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
    assert not hasattr(command, "__dict__")
    assert not hasattr(query, "__dict__")

    with pytest.raises(FrozenInstanceError):
        mutate_attribute(dto, name="name", value="Changed")

    with pytest.raises(FrozenInstanceError):
        mutate_attribute(command, name="title", value="Changed")

    with pytest.raises(FrozenInstanceError):
        mutate_attribute(query, name="id", value=2)


def test_use_case_input_bases_are_not_dto_bases() -> None:
    assert not issubclass(BaseCommand, BaseDTO)
    assert not issubclass(BaseQuery, BaseDTO)

    assert not isinstance(ExampleCommand(title="Write docs"), BaseDTO)
    assert not isinstance(ExampleQuery(id=1), BaseDTO)


def test_runtime_core_foundation_bases_are_importable() -> None:
    assert ExampleEnum.LOCAL.value == "local"
    assert issubclass(BaseEntity, object)
    assert issubclass(BaseApplicationError, Exception)
    assert issubclass(BaseApplicationValueError, ValueError)


def test_port_foundation_bases_enforce_abstract_contracts() -> None:
    assert isabstract(ExampleGateway)
    assert isabstract(ExampleRepository)
    assert isabstract(ExampleUnitOfWork)

    with pytest.raises(TypeError):
        instantiate_abstract(ExampleGateway)

    with pytest.raises(TypeError):
        instantiate_abstract(ExampleRepository)

    with pytest.raises(TypeError):
        instantiate_abstract(ExampleUnitOfWork)


def test_use_case_base_does_not_force_execute_signature() -> None:
    use_case = ExampleUseCase()

    assert isinstance(use_case, BaseUseCase)
