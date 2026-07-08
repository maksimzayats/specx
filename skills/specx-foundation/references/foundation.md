# Specx Foundation Reference

`foundation/` holds stable base classes and primitives used across layers. It
exists so project classes are never bare `class Foo:` declarations and do not
inherit raw external bases directly when a project-owned base exists.

## Suggested Package

```text
foundation/
  command.py
  configurator.py
  dto.py
  entity.py
  enums.py
  exceptions.py
  factory.py
  repository.py
  query.py
  service.py
  settings.py
  unit_of_work.py
  unit_of_work_manager.py
  use_case.py
  delivery/
    controller.py
    service.py
    fastapi/
      schema.py
  infrastructure/
    sqlalchemy/
      model.py
```

Create only the files needed by real classes. Plain marker bases in foundation
should use `class BaseThing:` with a scoped docstring and the smallest useful
body.

Concrete class names use the suffix implied by their foundation base ancestry:
`BaseCommand` -> `Command`, `BaseQuery` -> `Query`, `BaseDTO` -> `DTO`,
`BaseEntity` -> `Entity`, `BaseFastAPISchema` -> `Schema`,
`BaseUseCase` -> `UseCase`, `BaseService` -> `Service`,
`BaseRepository` -> `Repository`, `BaseUnitOfWork` -> `UnitOfWork`,
`BaseUnitOfWorkManager` -> `UnitOfWorkManager`, `BaseController` ->
`Controller`, `BaseFactory` -> `Factory`, `BaseConfigurator` ->
`Configurator`, `BaseRuntimeSettings` -> `Settings`, `BaseStrEnum` -> `Enum`,
`BaseDeliveryService` -> `Service`, `BaseApplicationError` -> `Error`,
`BaseApplicationValueError` -> `ValueError`, and `BaseSQLAlchemyModel` ->
`Model`.

## Base Catalog

Use these names unless the repo already has stronger local names:

- `BaseCommand` for state-changing use-case inputs.
- `BaseQuery` for read-only use-case inputs.
- `BaseDTO` for result DTOs and other core payloads.
- `BaseEntity` for framework-free entities and value objects.
- `BaseService` for focused reusable application behavior. Concrete core
  services still use the `Service` suffix.
- `BaseUseCase` for externally meaningful application actions.
- `BaseRepository` for repository/port contracts.
- `BaseUnitOfWork` for active unit-of-work contracts exposed inside manager
  scopes.
- `BaseUnitOfWorkManager` for objects that open, finish, and close active units
  of work.
- `BaseFactory` for dependency-injected factories and app factories.
- `BaseConfigurator` for bootstrap/configuration objects.
- `BaseRuntimeSettings` for `pydantic-settings` classes.
- `BaseStrEnum` for project enums.
- `BaseApplicationError` and `BaseApplicationValueError` for application
  exceptions.
- `BaseController` for delivery controllers.
- `BaseDeliveryService` for framework-facing helper services such as auth,
  request context, and rate limiting. Concrete delivery services still use the
  `Service` suffix.
- `BaseFastAPISchema` for FastAPI request and response schemas.
- `BaseSQLAlchemyModel` for SQLAlchemy declarative models when a real SQL
  adapter exists. It owns metadata naming conventions only, not engines,
  sessions, migrations, or schema creation.

## Minimal Examples

```python
from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base for core payloads represented as Pydantic models.

    Example:
        class TaskDTO(BaseDTO):
            id: int
            title: str
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)
```

```python
from order_service.foundation.dto import BaseDTO


class BaseCommand(BaseDTO):
    """Base for use-case inputs that request state-changing actions.

    Example:
        class CreateTaskCommand(BaseCommand):
            title: str
    """
```

```python
from order_service.foundation.dto import BaseDTO


class BaseQuery(BaseDTO):
    """Base for use-case inputs that request read-only results.

    Example:
        class GetTaskQuery(BaseQuery):
            task_id: int
    """
```

```python
class BaseService:
    """Base for focused reusable core behavior.

    Example:
        class OrderPricingService(BaseService):
            def calculate_total(self, *, subtotal: int) -> int:
                return subtotal
    """
```

```python
from enum import StrEnum


class BaseStrEnum(StrEnum):
    """Base for string enums used by settings and application values.

    Example:
        class EnvironmentEnum(BaseStrEnum):
            LOCAL = "local"
    """
```

```python
from abc import ABC, abstractmethod


class BaseUnitOfWork(ABC):
    """Base for active unit-of-work contracts exposed inside manager scopes.

    Example:
        class TaskUnitOfWork(BaseUnitOfWork):
            def _unit_of_work_marker(self) -> None:
                return None

            @property
            def tasks(self) -> TaskRepository:
                return self._tasks
    """

    @abstractmethod
    def _unit_of_work_marker(self) -> None:
        raise NotImplementedError
```

```python
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Literal

from order_service.foundation.unit_of_work import BaseUnitOfWork


class BaseUnitOfWorkManager[UnitOfWorkT: BaseUnitOfWork](ABC):
    """Base for objects that open, finish, and close active units of work.

    Example:
        class TaskUnitOfWorkManager(BaseUnitOfWorkManager[TaskUnitOfWork]):
            async def __aenter__(self) -> TaskUnitOfWork:
                return self._unit_of_work
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWorkT:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        raise NotImplementedError
```

```python
class BaseDeliveryService:
    """Base for delivery-layer helper services.

    Example:
        class BearerTokenParsingService(BaseDeliveryService):
            def parse(self, *, authorization_header: str) -> str:
                return authorization_header.removeprefix("Bearer ")
    """
```

```python
from abc import ABC, abstractmethod
from typing import Any


class BaseController(ABC):
    """Base for delivery controllers that register routes.

    Example:
        class TasksController(BaseController):
            def register(self, registry: APIRouter) -> None:
                registry.add_api_route("/api/v1/tasks", self.list_tasks)
    """

    @abstractmethod
    def register(self, registry: Any) -> None:
        raise NotImplementedError
```

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSQLAlchemyModel(DeclarativeBase):
    """Base for SQLAlchemy declarative models.

    Example:
        class TaskModel(BaseSQLAlchemyModel):
            __tablename__ = "tasks"
    """

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
```

## Usage Examples

```python
from dataclasses import dataclass

from order_service.foundation.service import BaseService


@dataclass(kw_only=True, slots=True)
class OrderPricingService(BaseService):
    """Service that prices orders.

    Example:
        total = service.price(subtotal=10)
    """

    def price(self, *, subtotal: int) -> int:
        return subtotal
```

```python
from order_service.foundation.dto import BaseDTO


class CreateOrderResultDTO(BaseDTO):
    """Result DTO returned after order creation.

    Example:
        CreateOrderResultDTO(order_id=1)
    """

    order_id: int
```

```python
from order_service.foundation.delivery.fastapi.schema import BaseFastAPISchema


class OrderResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for an order.

    Example:
        OrderResponseSchema(id=1, title="Write docs")
    """

    id: int
    title: str
```

Major concrete classes should also have a scoped docstring with a concrete
`Example:`. This includes use cases, services, repositories, adapters,
controllers, factories, settings, DTOs, entities, schemas, unit-of-work ports,
and unit-of-work managers.

## Extension Rule

It is fine to extend foundation with a new base class when a real class category
appears and no existing base fits. Add the smallest useful base, name it after
the category, and update architecture tests if the new base replaces a raw
external base.

Do not add foundation bases speculatively. A base class must serve code that
exists now.

## Architecture Guardrails

Useful checks:

- non-foundation source classes have at least one explicit base;
- foundation classes have scoped docstrings with concrete examples;
- major non-foundation classes have scoped docstrings with concrete examples;
- class names use the suffix implied by their foundation base ancestry;
- non-foundation classes do not directly inherit `BaseModel`, `BaseSettings`,
  `ABC`, `Exception`, `ValueError`, `DeclarativeBase`, `StrEnum`, or `object`;
- foundation does not import `core`, `delivery`, `ioc`, or scope
  infrastructure;
- foundation SQLAlchemy bases do not create engines, sessions, migrations, or
  database schema;
- `__init__.py` files stay empty.
