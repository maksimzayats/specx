# Specx Service Reference

Services own focused reusable core behavior. Delivery-only helpers such as
auth dependencies, rate limiting, and request-context adapters live under
`delivery/`, not `core/<scope>/services/`.

Do not call small collaborators services by default. Use `Service` for reusable
business/application behavior. Use `BaseCapability` for small replaceable abilities
that do one narrow thing, can be faked or swapped, and do not own workflows,
UoW scopes, repositories, or gateways.

## Class Shape

```python
from dataclasses import dataclass

from diwire import Injected

from specx.foundation.pure_service import BasePureService


@dataclass(kw_only=True, slots=True)
class OrderPricingService(BasePureService):
    """Service that prices orders from items and tax policy.

    Example:
        total = service.price(items=(OrderItem(price=Money("10.00")),))
    """

    _tax_policy_service: Injected[TaxPolicyService]

    def price(self, *, items: tuple[OrderItem, ...]) -> Money:
        subtotal = sum((item.price for item in items), Money.zero())
        tax = self._tax_policy_service.calculate_tax(amount=subtotal)
        return subtotal + tax
```

Choose `BasePureService`, `BaseReadService`, or `BaseEffectService` and use
`Injected[...]` for dependencies. Keep methods keyword-only. Every service
class name must end with `Service`. Do not add or use a generic `BaseService`.

## Service Base Choice

Use `BasePureService` for deterministic business helpers.

Allowed:

- primitives;
- entities passed as arguments;
- value objects;
- DTOs when needed;
- other pure services.

Forbidden:

- `UnitOfWorkManager`;
- active `UnitOfWork`;
- repositories;
- gateways;
- clients;
- settings;
- clocks;
- UUID generators;
- random/time;
- HTTP;
- SQLAlchemy;
- Redis;
- OpenAI SDK.

Use `BaseReadService` for read-only orchestration helpers.

Allowed:

- repository reads, preferably through an active UoW passed by the caller;
- read gateways;
- pure services;
- DTO mapping.

Forbidden:

- commit/rollback;
- `UnitOfWorkManager`;
- repository mutators;
- external write gateways;
- message publishing;
- sending email;
- charging money.

Use `BaseEffectService` for helpers that perform or coordinate side effects.

Allowed:

- effect gateways;
- active UoW passed by a command use case;
- repository mutators through that active UoW;
- pure services.

Forbidden:

- opening UoW scopes;
- owning transaction lifecycle;
- returning entities outward;
- importing delivery/framework code.

## Dependency Choice

Inject a concrete class when:

- it is project-owned;
- it has no external IO;
- there is one implementation;
- tests can use it deterministically.

An in-memory dependency is acceptable as a concrete core service only when it is
deliberately part of the application behavior or a starter/demo implementation
with no external IO. Name it honestly with the `Service` suffix, for example
`OrderSummaryStoreService` or `StaticCatalogService`, and keep it under
`services/` only while it has no database, network, filesystem, Redis, clock, or
randomness dependency. If it is just one small replaceable ability, make it a
`BaseCapability` under `core/<scope>/capabilities/` instead. Move it behind a core
gateway port and infrastructure adapter as soon as it becomes external IO.

Inject a core repository or gateway port when:

- it wraps external IO;
- it hides a framework or SDK;
- it has multiple real implementations;
- replacing it in tests is important.

Repository ports live under `core/<scope>/repositories/` and model owned
persistence. Gateway ports live under `core/<scope>/gateways/` and model
outbound business capabilities such as OpenAI summaries, payments, email, or
external APIs.

## UoW Parameters

Read/effect services may receive an active UoW as a method argument:

```python
from specx.foundation.read_service import BaseReadService


@dataclass(kw_only=True, slots=True)
class TaskLookupService(BaseReadService):
    """Service that reads task DTOs from an active task unit of work.

    Example:
        task = await service.get(unit_of_work=unit_of_work, task_id=1)
    """

    async def get(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
        task = await unit_of_work.tasks.get(task_id=task_id)
        if task is None:
            raise TaskNotFoundError(task_id=task_id)
        return TaskDTO(id=task.id, title=task.title, is_completed=task.is_completed)
```

The service does not open `async with self._unit_of_work_manager`. The use case
owns the transaction:

```python
async with self._unit_of_work_manager as unit_of_work:
    return await self._task_completion_service.complete(
        unit_of_work=unit_of_work,
        task_id=command.task_id,
    )
```

This service implementation is wrong because it hides transaction lifecycle:

```python
async with self._unit_of_work_manager as unit_of_work:
    ...
```

Effect services follow the same active-UoW rule:

```python
from specx.foundation.effect_service import BaseEffectService


@dataclass(kw_only=True, slots=True)
class TaskCompletionService(BaseEffectService):
    """Service that completes tasks inside an active task unit of work.

    Example:
        task = await service.complete(unit_of_work=unit_of_work, task_id=1)
    """

    async def complete(self, *, unit_of_work: TaskUnitOfWork, task_id: int) -> TaskDTO:
        task = await unit_of_work.tasks.complete(task_id=task_id)
        if task is None:
            raise TaskNotFoundError(task_id=task_id)
        return TaskDTO(id=task.id, title=task.title, is_completed=task.is_completed)
```

## Unit Tests

Construct services directly unless DI behavior is the subject:

```python
def test_order_pricer_adds_tax() -> None:
    service = OrderPricingService(
        _tax_policy_service=FixedTaxPolicyService(rate=Decimal("0.20")),
    )

    result = service.price(items=(OrderItem(price=Money("10.00")),))

    assert result == Money("12.00")
```

## Avoid

- No `Manager`, `Helper`, `Utils`, or vague `Handler` names.
- No small swappable ability modeled as a service; use `BaseCapability`.
- No framework imports.
- No SQLAlchemy/Redis/HTTP clients.
- No transaction scopes.
- No direct environment reads.
- No bare service classes.
- No service class without the `Service` suffix.
