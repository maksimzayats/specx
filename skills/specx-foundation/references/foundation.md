# Specx Foundation Reference

`foundation/` holds stable base classes and primitives used across layers. It
exists so project classes are never bare `class Foo:` declarations and do not
inherit raw external bases directly when a project-owned base exists.

## Suggested Package

```text
foundation/
  capability.py
  command.py
  configurator.py
  dto.py
  entity.py
  enums.py
  exceptions.py
  factory.py
  gateway.py
  effect_service.py
  pure_service.py
  read_service.py
  repository.py
  query.py
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

Create only the files needed by real classes. Foundation modules should use
unprefixed filenames such as `capability.py`, `gateway.py`, and
`pure_service.py`. Foundation class names stay prefixed, for example
`BaseCapability`, `BaseGateway`, `BasePureService`, `BaseReadService`, and
`BaseEffectService`. New narrower capability-family bases stay prefixed too,
for example `BaseClock` or `BaseGenerator`.

Concrete class names use the suffix implied by their foundation base ancestry:
`BaseCommand` -> `Command`, `BaseQuery` -> `Query`, `BaseDTO` -> `DTO`,
`BaseEntity` -> `Entity`, `BaseFastAPISchema` -> `Schema`,
`BaseUseCase` -> `UseCase`, `BaseCapability` -> `Capability`,
`BaseGateway` -> `Gateway`, `BasePureService` / `BaseReadService` /
`BaseEffectService` -> `Service`, `BaseRepository` -> `Repository`,
`BaseUnitOfWork` -> `UnitOfWork`, `BaseUnitOfWorkManager` ->
`UnitOfWorkManager`, `BaseController` -> `Controller`, `BaseFactory` ->
`Factory`, `BaseConfigurator` -> `Configurator`, `BaseRuntimeSettings` ->
`Settings`, `BaseStrEnum` -> `Enum`, `BaseDeliveryService` -> `Service`,
`BaseApplicationError` -> `Error`, `BaseApplicationValueError` ->
`ValueError`, and `BaseSQLAlchemyModel` -> `Model`.

Direct concrete subclasses of `BaseCapability` use the `Capability` suffix.
When a capability family becomes common or needs stronger review rules, add a
narrower foundation base inheriting `BaseCapability`; concrete classes then use
the narrower suffix, for example `BaseClock` -> `SystemClock` and
`BaseGenerator` -> `UUID7Generator`.

## Base Catalog

Use these names unless the repo already has stronger local names:

- `BaseCommand` for state-changing use-case inputs.
- `BaseQuery` for read-only use-case inputs.
- `BaseDTO` for result DTOs and other core payloads.
- `BaseEntity` for framework-free entities and value objects.
- `BaseCapability` for small injectable collaborators that do one narrow thing,
  may be faked or swapped, and do not own application workflows, UoW scopes,
  repositories, or gateways.
- `BaseGateway` for core-facing outbound business capability ports to external
  systems. Gateway ports live under `core/<scope>/gateways/`, use business
  language, declare external effects, and do not return entities.
- `BasePureService` for deterministic core helpers with no IO, UoW,
  repository, gateway, client, settings, clock, UUID, random, time, SQLAlchemy,
  Redis, OpenAI SDK, or framework dependency.
- `BaseReadService` for read-only orchestration helpers that may read through
  repositories/read gateways, preferably via an active UoW passed by the caller.
- `BaseEffectService` for helpers that perform or coordinate side effects
  through an active UoW or effect gateways. They must not open UoW scopes.
- `BaseUseCase` for externally meaningful application actions.
- `BaseRepository` for owned-persistence repository ports and adapters.
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
class BaseCapability:
    """Base class for small injectable collaborators.

    Capabilities do one narrow thing, may be injected or faked, and do not own
    application workflows, unit-of-work scopes, repositories, or gateways.

    Example:
        SlugGeneratingCapability creates slugs for display labels.
        BaseClock can be introduced later for concrete clocks such as SystemClock.
        BaseGenerator can be introduced later for classes such as UUID7Generator.
    """
```

```python
class BaseGateway:
    """Base class for outbound business capabilities.

    Gateways are core-facing interfaces to external systems. A gateway should
    expose business language, not SDK or HTTP details.

    Example:
        TaskSummaryGateway generates summaries for task descriptions.
        PaymentGateway charges customers.
        EmailGateway sends transactional emails.
    """
```

```python
class BasePureService:
    """Base class for deterministic business helpers.

    Pure services do not perform I/O, do not use repositories, do not use
    gateways, and do not depend on unit-of-work objects, settings, clocks,
    UUID generators, random numbers, HTTP clients, SQLAlchemy, Redis, or SDKs.

    Example:
        class TaskTitleNormalizerService(BasePureService):
            def normalize(self, *, title: str) -> str:
                return " ".join(title.split())
    """
```

```python
class BaseReadService:
    """Base class for read-only orchestration helpers.

    Read services may read from repositories or read gateways, usually through
    an active unit of work passed by the caller. They may map entities to DTOs,
    but they must not commit, roll back, call repository mutators, publish
    messages, send email, charge money, or call external write APIs.

    Example:
        class TaskLookupService(BaseReadService):
            async def get(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
                task = await unit_of_work.tasks.get(task_id=task_id)
                return TaskDTO.model_validate(task)
    """
```

```python
class BaseEffectService:
    """Base class for helpers that perform or coordinate side effects.

    Effect services may mutate owned state through an active unit of work
    passed by a use case, or call outbound gateways with real side effects.
    They must not open unit-of-work scopes, own transaction lifecycle, return
    entities outward, or import delivery/framework code.

    Example:
        class TaskCompletionService(BaseEffectService):
            async def complete(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
                task = await unit_of_work.tasks.complete(task_id=task_id)
                return TaskDTO.model_validate(task)
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

from order_service.foundation.pure_service import BasePureService


@dataclass(kw_only=True, slots=True)
class OrderPricingService(BasePureService):
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
- direct concrete `BaseCapability` subclasses use the `Capability` suffix;
- narrower foundation bases inheriting `BaseCapability` use their narrower
  suffix, for example `BaseClock` -> `SystemClock`;
- capabilities do not open UoW scopes, inherit repository/gateway bases, or use
  generic `Helper`, `Utils`, `Manager`, or `Dependency` names;
- gateway ports live under `core/<scope>/gateways/`, concrete gateway
  implementations live under `core/<scope>/infrastructure/<technology>/`,
  gateway docstrings declare external effects, and gateway methods do not
  return entities;
- core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`, not a generic `BaseService`;
- pure services do not import IO/runtime-state dependencies;
- read services do not call repository mutators or transaction lifecycle
  methods;
- effect services do not inject UoW managers, open UoW scopes, commit, roll
  back, return entities outward, or import delivery/framework code;
- non-foundation classes do not directly inherit `BaseModel`, `BaseSettings`,
  `ABC`, `Exception`, `ValueError`, `DeclarativeBase`, `StrEnum`, or `object`;
- foundation does not import `core`, `delivery`, `ioc`, or scope
  infrastructure;
- foundation SQLAlchemy bases do not create engines, sessions, migrations, or
  database schema;
- `__init__.py` files stay empty.
