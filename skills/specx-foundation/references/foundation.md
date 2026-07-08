# Specx Foundation Reference

Specx ships reusable foundation bases in the `specx.foundation` package. New
services should import those bases directly instead of generating a large
project-local foundation tree.

Prefer standard-library dataclasses for core data classes unless the user asks
for another model type. Commands, queries, DTOs, and entities should normally
use `@dataclass(frozen=True, kw_only=True, slots=True)`. Keep Pydantic at the
delivery/schema and settings edges.

Create `src/<package>/foundation/` only when current code has a real class
category that `specx.foundation` does not cover. Keep local foundation modules
small and stable.

## Packaged Bases

Use these imports first:

| Base | Import path | Use for |
| --- | --- | --- |
| `BaseDTO` | `specx.foundation.dto` | Core result DTOs and application payloads. |
| `BaseCommand` | `specx.foundation.command` | State-changing use-case inputs. |
| `BaseQuery` | `specx.foundation.query` | Read-only use-case inputs. |
| `BaseEntity` | `specx.foundation.entity` | Framework-free entities and value objects. |
| `BaseUseCase` | `specx.foundation.use_case` | Externally meaningful application actions. |
| `BasePureService` | `specx.foundation.pure_service` | Deterministic helpers with no IO or runtime state. |
| `BaseReadService` | `specx.foundation.read_service` | Read-only orchestration helpers. |
| `BaseEffectService` | `specx.foundation.effect_service` | Helpers that coordinate side effects without opening UoW scopes. |
| `BaseCapability` | `specx.foundation.capability` | Small injectable collaborators narrower than services. |
| `BaseGateway` | `specx.foundation.gateway` | Core-facing outbound business capability ports. |
| `BaseRepository` | `specx.foundation.repository` | Owned-persistence repository ports and adapters. |
| `BaseUnitOfWork` | `specx.foundation.unit_of_work` | Active unit-of-work contracts. |
| `BaseUnitOfWorkManager` | `specx.foundation.unit_of_work_manager` | Objects that open, finish, and close active UoWs. |
| `BaseFactory` | `specx.foundation.factory` | Dependency-injected factories and app factories. |
| `BaseConfigurator` | `specx.foundation.configurator` | Bootstrap/configuration objects. |
| `BaseRuntimeSettings` | `specx.foundation.settings` | `pydantic-settings` runtime settings. |
| `BaseStrEnum` | `specx.foundation.enums` | String enums used by settings and application values. |
| `BaseApplicationError` | `specx.foundation.exceptions` | Application errors translated by delivery layers. |
| `BaseApplicationValueError` | `specx.foundation.exceptions` | Invalid application values rejected before persistence. |
| `BaseController` | `specx.foundation.delivery.controller` | Delivery controllers that register public routes. |
| `BaseDeliveryService` | `specx.foundation.delivery.service` | Delivery-only helpers such as auth or rate limiting. |
| `BaseFastAPISchema` | `specx.foundation.delivery.fastapi.schema` | FastAPI request and response schemas. |
| `BaseSQLAlchemyModel` | `specx.foundation.infrastructure.sqlalchemy.model` | SQLAlchemy declarative models and metadata naming conventions. |

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
- `BaseSQLAlchemyModel` -> `Model`

Direct concrete subclasses of `BaseCapability` use the `Capability` suffix.
When a capability family needs stronger review rules, add a project-local
narrower base that inherits `BaseCapability`, such as `BaseClock` or
`BaseGenerator`; concrete classes then use the narrower suffix, for example
`SystemClock` or `UUID7Generator`.

## Usage Examples

```python
from dataclasses import dataclass

from specx.foundation.dto import BaseDTO
from specx.foundation.entity import BaseEntity


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

from specx.foundation.pure_service import BasePureService


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

from specx.foundation.command import BaseCommand
from specx.foundation.use_case import BaseUseCase


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateOrderCommand(BaseCommand):
    """Command for creating an order.

    Example:
        CreateOrderCommand(customer_id=1)
    """

    customer_id: int


class CreateOrderUseCase(BaseUseCase):
    """Use case that creates orders.

    Example:
        result = use_case.execute(command=command)
    """
```

```python
from specx.foundation.delivery.fastapi.schema import BaseFastAPISchema


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

- current code has a real class category;
- no packaged `specx.foundation` base describes that category;
- the category improves architecture checks, naming, or dependency boundaries.

Place it under `src/<package>/foundation/<category>.py`. Do not use `base_`
module prefixes. Class names stay prefixed, for example `clock.py` defines
`BaseClock`.

Good local extension:

```python
from specx.foundation.capability import BaseCapability


class BaseClock(BaseCapability):
    """Base for injectable time sources.

    Example:
        class SystemClock(BaseClock):
            def now(self) -> datetime:
                return datetime.now(UTC)
    """
```

Avoid local copies of packaged bases such as `BaseDTO`, `BaseUseCase`, or
`BasePureService`.

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
