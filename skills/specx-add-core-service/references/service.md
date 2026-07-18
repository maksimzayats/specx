# specx Service Reference

Services own focused reusable core behavior. Delivery-only helpers such as
auth dependencies, rate limiting, and request-context adapters live under
`delivery/`, not `core/<scope>/services/`.

## Contents

- [Class shape](#class-shape)
- [Service base choice](#service-base-choice)
- [Dependency choice](#dependency-choice)
- [UoW parameters](#uow-parameters)
- [Unit tests](#unit-tests)
- [Avoid](#avoid)

Do not call small collaborators services by default. Use `Service` for reusable
business/application behavior. Use `BaseCapability` for small replaceable
abilities that do one narrow thing, can be replaced in tests, and do not own
workflows, UoW scopes, repositories, or gateways.

## Class Shape

```python
from dataclasses import dataclass
from decimal import Decimal

from diwire import Injected

from order_service.core.orders.capabilities.tax_rate_capability import TaxRateCapability
from specx.core.foundation.pure_service import BasePureService


@dataclass(kw_only=True, slots=True)
class OrderPricingService(BasePureService):
    """Service that adds the current tax rate to an order subtotal.

    Example:
        total = service.price(subtotal=Decimal("10.00"))
    """

    _tax_rate_capability: Injected[TaxRateCapability]

    def price(self, *, subtotal: Decimal) -> Decimal:
        tax = subtotal * self._tax_rate_capability.current_rate()
        return subtotal + tax
```

Choose `BasePureService`, `BaseReadService`, or `BaseEffectService` and use
`Injected[...]` for dependencies. Keep methods keyword-only. Every service
class name must end with `Service`. Do not add or use a generic `BaseService`.

## Service Base Choice

Use `BasePureService` for deterministic business helpers. Pure services do not
depend on UoWs, repositories, gateways, clients, settings, clocks, random/time,
SQLAlchemy, Redis, or SDKs.

Use `BaseReadService` for read-only orchestration helpers. They may read
repositories through an active UoW passed by the caller, use read gateways, and
map DTOs. They must not commit, roll back, call repository mutators, or use
external write gateways.

Use `BaseEffectService` for helpers that perform or coordinate side effects.
They may use effect gateways or repository mutators through an active UoW
passed by a command use case. They do not open UoW scopes or own transaction
lifecycle.

A database rollback cannot undo an already completed gateway call. When one
workflow must persist state and notify another system, make the consistency
policy explicit: prefer recording an outbox/intent in the UoW and dispatching
it separately, or define idempotency, retry, and compensation behavior. Do not
present a database transaction plus an external call as one atomic operation.

`ReadinessProbeService` is a valid read service when it coordinates readiness
gateway ports and returns core DTOs. It must not import SQLAlchemy, Redis,
FastAPI, or top-level infrastructure directly; put those checks in
`core/health/infrastructure/<technology>/` gateway adapters. Each adapter must
use a short timeout appropriate for operational probing.

## Dependency Choice

Inject a concrete class when it is project-owned, has no external IO, has one
implementation, and tests can use it deterministically.

Inject a repository port for persistence owned by the service. Inject a
gateway port for an outbound business capability supplied by another system,
especially when it hides a framework or SDK or has multiple real
implementations. Repository ports live under `core/<scope>/repositories/`;
gateway ports live under `core/<scope>/gateways/`. Do not introduce an
interface solely for mocking; unit tests can override a concrete dependency in
the test container.

## UoW Parameters

Read/effect services may receive an active UoW as a method argument:

```python
from specx.core.foundation.read_service import BaseReadService


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

The use case owns the transaction:

```python
async with self._unit_of_work_manager as unit_of_work:
    return await self._task_lookup_service.get(
        unit_of_work=unit_of_work,
        task_id=query.task_id,
    )
```

## Unit Tests

Service tests mirror the source path directly and resolve the service from the
native pytest `container` fixture:

```text
tests/unit/core/orders/services/test_order_pricing_service.py
```

One-off class-based doubles live in the same test module that uses them:

```python
from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class FixedTaxRateCapability(TaxRateCapability):
    """Fixed tax-rate capability for order pricing tests.

    Example:
        capability = FixedTaxRateCapability(rate=Decimal("0.20"))
    """

    rate: Decimal

    def current_rate(self) -> Decimal:
        return self.rate


def test_order_pricer_adds_tax(container: Container) -> None:
    capability = FixedTaxRateCapability(rate=Decimal("0.20"))
    container.add_instance(capability, provides=TaxRateCapability)
    service = container.resolve(OrderPricingService)

    result = service.price(subtotal=Decimal("10.00"))

    assert result == Decimal("12.0000")
```

Use inline `MagicMock`, `AsyncMock`, or `create_autospec` in the test body when
only one behavior needs to change for that scenario. Give mocks at least a
spec; prefer `create_autospec(..., instance=True, spec_set=True)` because it
also rejects invalid call signatures. Reused unit-test doubles may live in mirrored
`tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
modules. Do not create per-target folders, `harness.py`, target factories,
target harnesses, `tests/_support/fakes`, shared `_fakes.py` files, fake
modules outside those mirrored unit port/capability packages, or double classes
in `conftest.py`.

## Avoid

- No `Manager`, `Helper`, `Utils`, or vague `Handler` names.
- No small swappable ability modeled as a service; use `BaseCapability`.
- No framework imports.
- No SQLAlchemy/Redis/HTTP clients.
- No transaction scopes.
- No direct environment reads.
- No bare service classes.
- No service class without the `Service` suffix.
