# Specx Foundation Reference

Specx ships reusable foundation bases in scoped packages. New services should
import those bases directly instead of generating a large project-local
foundation tree:

- `specx.core.foundation` for core commands, queries, DTOs, entities, use
  cases, services, ports, UoWs, factories, enums, and exceptions.
- `specx.delivery.foundation` for delivery controllers, delivery services, and
  framework schema bases.
- `specx.infrastructure.foundation` for runtime settings, configurators, and
  infrastructure-specific bases such as SQLAlchemy model bases.

Prefer standard-library dataclasses for core data classes unless the user asks
for another model type. Commands, queries, DTOs, and entities should normally
use `@dataclass(frozen=True, kw_only=True, slots=True)`. Keep Pydantic at the
delivery/schema and settings edges.

`BaseCommand` and `BaseQuery` are independent use-case input bases, not
subclasses of `BaseDTO`. Keep input contracts separate from output DTOs so
architecture checks, type checks, and human review can distinguish what enters
a use case from what crosses an output boundary.

When a value has a limited known set, use a `BaseStrEnum` with the `Enum`
suffix instead of a plain `str` or `Literal[...]`. This keeps accepted values
discoverable, reusable across core/delivery/tests, and protected by foundation
suffix guardrails.

Port-style bases that host project abstract methods are ABCs. `BaseGateway`,
`BaseRepository`, `BaseUnitOfWork`, and `BaseUnitOfWorkManager` support
`@abstractmethod` enforcement so DI cannot accidentally instantiate an
unimplemented project port. `BaseUseCase` intentionally does not define an
abstract `execute(...)` because use-case signatures differ by command/query
type.

Do not create an empty local `foundation/` package. Create
`src/<package>/foundation/` only when current code has a real project-local base
category or a stateful framework base that must not be shared globally, such as
the project SQLAlchemy declarative base. Keep local foundation modules small
and stable.

## Packaged Bases

Use these imports first:

| Base | Import path | Use for |
| --- | --- | --- |
| `BaseDTO` | `specx.core.foundation.dto` | Core result DTOs and application output payloads, not use-case inputs. |
| `BaseCommand` | `specx.core.foundation.command` | State-changing use-case inputs. |
| `BaseQuery` | `specx.core.foundation.query` | Read-only use-case inputs. |
| `BaseEntity` | `specx.core.foundation.entity` | Framework-free entities and value objects. |
| `BaseUseCase` | `specx.core.foundation.use_case` | Externally meaningful application actions. |
| `BasePureService` | `specx.core.foundation.pure_service` | Deterministic helpers with no IO or runtime state. |
| `BaseReadService` | `specx.core.foundation.read_service` | Read-only orchestration helpers. |
| `BaseEffectService` | `specx.core.foundation.effect_service` | Helpers that coordinate side effects without opening UoW scopes. |
| `BaseCapability` | `specx.core.foundation.capability` | Small injectable collaborators narrower than services. |
| `BaseGateway` | `specx.core.foundation.gateway` | Core-facing outbound business capability ports. |
| `BaseRepository` | `specx.core.foundation.repository` | Owned-persistence repository ports and adapters. |
| `BaseUnitOfWork` | `specx.core.foundation.unit_of_work` | Active unit-of-work contracts. |
| `BaseUnitOfWorkManager` | `specx.core.foundation.unit_of_work_manager` | Objects that open, finish, and close active UoWs. |
| `BaseFactory` | `specx.core.foundation.factory` | Dependency-injected factories and app factories. |
| `BaseConfigurator` | `specx.infrastructure.foundation.configurator` | Bootstrap/configuration objects. |
| `BaseRuntimeSettings` | `specx.infrastructure.foundation.settings` | `pydantic-settings` runtime settings. |
| `BaseStrEnum` | `specx.core.foundation.enums` | String enums used by settings and application values. |
| `BaseApplicationError` | `specx.core.foundation.exceptions` | Application errors translated by delivery layers. |
| `BaseApplicationValueError` | `specx.core.foundation.exceptions` | Invalid application values rejected before persistence. |
| `BaseController` | `specx.delivery.foundation.controller` | Delivery controllers that register public routes. |
| `BaseDeliveryService` | `specx.delivery.foundation.service` | Delivery-only helpers such as auth or rate limiting. |
| `BaseFastAPISchema` | `specx.delivery.foundation.fastapi.schema` | FastAPI request and response schemas. |
| `BaseSQLAlchemyModel` | `specx.infrastructure.foundation.sqlalchemy.model` | Infrastructure SQLAlchemy model bases. Generated services usually define a project-local SQLAlchemy base instead. |

## Naming Rules

Concrete class names use the suffix implied by their most-specific base:

- `BaseCommand` -> `Command`
- `BaseQuery` -> `Query`
- `BaseDTO` -> `DTO`
- `BaseEntity` -> `Entity`
- `BaseFastAPISchema` -> `Schema`
- `BaseUseCase` -> `UseCase`
- `BaseCapability` -> `Capability`
- `BaseGateway` -> `Gateway`
- `BasePureService`, `BaseReadService`, `BaseEffectService` -> `Service`
- `BaseRepository` -> `Repository`
- `BaseUnitOfWork` -> `UnitOfWork`
- `BaseUnitOfWorkManager` -> `UnitOfWorkManager`
- `BaseController` -> `Controller`
- `BaseFactory` -> `Factory`
- `BaseRuntimeSettings` -> `Settings`
- `BaseApplicationError` -> `Error`
- `BaseApplicationValueError` -> `ValueError`
- project-local `BaseSQLAlchemyModel` -> `Model`

Direct concrete subclasses of `BaseCapability` use the `Capability` suffix.
When a capability family needs stronger review rules, add a project-local
narrower base that inherits `BaseCapability`, such as `BaseClock` or
`BaseGenerator`; concrete classes then use the narrower suffix, for example
`SystemClock` or `UUID7Generator`.

## Usage Examples

```python
from dataclasses import dataclass

from specx.core.foundation.dto import BaseDTO
from specx.core.foundation.entity import BaseEntity


@dataclass(frozen=True, kw_only=True, slots=True)
class OrderDTO(BaseDTO):
    """DTO returned from order use cases.

    Example:
        OrderDTO(id=1, total=100)
    """

    id: int
    total: int


@dataclass(frozen=True, kw_only=True, slots=True)
class OrderEntity(BaseEntity):
    """Framework-free order state used inside core.

    Example:
        OrderEntity(id=1, total=100)
    """

    id: int
    total: int
```

```python
from dataclasses import dataclass

from specx.core.foundation.pure_service import BasePureService


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
from dataclasses import dataclass

from specx.core.foundation.command import BaseCommand
from specx.core.foundation.query import BaseQuery


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateOrderCommand(BaseCommand):
    """Command for creating an order.

    Example:
        CreateOrderCommand(customer_id=1)
    """

    customer_id: int


@dataclass(frozen=True, kw_only=True, slots=True)
class ListOrdersQuery(BaseQuery):
    """Query for listing orders.

    Example:
        ListOrdersQuery()
    """
```

```python
from specx.core.foundation.use_case import BaseUseCase


class CreateOrderUseCase(BaseUseCase):
    """Use case that creates orders.

    Example:
        result = use_case.execute(command=command)
    """
```

```python
from specx.core.foundation.enums import BaseStrEnum


class OrderStatusEnum(BaseStrEnum):
    """Enum for order lifecycle states.

    Example:
        OrderStatusEnum.CREATED
    """

    CREATED = "created"
    PAID = "paid"
```

```python
from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema


class OrderResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for an order.

    Example:
        OrderResponseSchema(id=1, title="Write docs")
    """

    id: int
    title: str
```

## Local Extension Rule

Add a project-local foundation base only when all are true:

- current code has a real project-local base category or a stateful framework
  base;
- no packaged scoped foundation base describes that category, or the
  base owns project-local framework state such as SQLAlchemy `MetaData`;
- the category improves architecture checks, naming, or dependency boundaries.

Place it under `src/<package>/foundation/<category>.py`. Do not use `base_`
module prefixes. Class names stay prefixed, for example `clock.py` defines
`BaseClock`.

Good local extension:

```python
from specx.core.foundation.capability import BaseCapability


class BaseClock(BaseCapability):
    """Base for injectable time sources.

    Example:
        class SystemClock(BaseClock):
            def now(self) -> datetime:
                return datetime.now(UTC)
    """
```

Good stateful framework extension:

```python
from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSQLAlchemyModel(DeclarativeBase):
    """Project-local SQLAlchemy declarative base.

    Example:
        class OrderModel(BaseSQLAlchemyModel):
            __tablename__ = "orders"
    """

    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
```

Avoid local copies of packaged bases such as `BaseDTO`, `BaseUseCase`, or
`BasePureService`. A project-local SQLAlchemy declarative base is not a copy of
a stateless packaged base; it owns project-specific metadata.

## Guardrails

Useful checks:

- non-foundation source classes inherit explicit packaged or local bases;
- major classes have scoped docstrings with concrete `Example:` blocks;
- class names use the suffix implied by the most-specific base;
- capabilities do not act as services, repositories, gateways, helpers,
  managers, or generic dependencies;
- gateway ports live under `core/<scope>/gateways/`, declare external effects,
  and do not return entities;
- core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`, not a generic `BaseService`;
- non-foundation classes do not directly inherit raw common bases such as
  `BaseModel`, `BaseSettings`, `ABC`, `Exception`, `ValueError`,
  `DeclarativeBase`, `StrEnum`, or `object`;
- local foundation modules, if present, do not import `core`, `delivery`,
  `ioc`, scope infrastructure, or application logic;
- local SQLAlchemy bases, if added, do not create engines, sessions,
  migrations, or database schema.
