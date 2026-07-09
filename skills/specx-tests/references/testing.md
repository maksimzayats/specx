# Specx Testing Reference

Tests prove behavior and protect boundaries while `diwire` assembles project
graphs through native pytest fixtures. Core test bodies receive `container`,
register scenario-specific overrides directly, resolve the target class, then
exercise behavior.

## Layout

Mirror source paths under the test layer that owns the behavior:

```text
tests/
  _support/
    clients/
    db/
    integration.py
  guardrails/
    architecture/test_boundaries.py
  unit/
    conftest.py
    core/
      <scope>/
        services/test_<service_module>.py
        use_cases/test_<use_case_module>.py
        capabilities/test_<capability_module>.py
  integration/
    conftest.py
    core/
      <scope>/use_cases/test_<use_case_module>.py
    delivery/<framework>/
    migrations/test_alembic.py
```

Create only folders that contain real tests or mirrored fake modules. Private
support code lives under `tests/_support` and must stay generic: clients, DB
helpers, and shared integration resources. Do not create
`tests/_support/fakes`, `tests/**/_fakes.py`, per-target folders, `harness.py`,
or `_scenarios.py`. One-off class-based doubles belong in the `test_*.py`
module that uses them. Reused class-based doubles may live in mirrored
`tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
modules. Every directory under `tests/` has an empty `__init__.py`.

The required mirrored scope is currently only core services, use cases, and
capabilities. Do not create repository, UoW, model, session, or adapter tests
only to mirror source files.

## Unit Tests

Unit tests use a fresh test container. The default fixture is a bare container:

```python
import pytest
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy


@pytest.fixture
def container() -> Container:
    return Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
```

Resolve project classes from the container. Register overrides before resolving
the target:

```python
from dataclasses import dataclass

import pytest
from diwire import Container


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

    result = service.price(items=(OrderItem(price=Money("10.00")),))

    assert result == Money("12.00")
```

Use inline mocks when a scenario only needs one collaborator behavior changed:

```python
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.anyio
async def test_execute_rolls_back_when_creation_fails(container: Container) -> None:
    creation_service = MagicMock(spec=ShortUrlCreationService)
    creation_service.create = AsyncMock(side_effect=ShortCodeCollisionError(max_attempts=5))
    unit_of_work_manager = TrackingShortUrlUnitOfWorkManager()

    container.add_instance(creation_service, provides=ShortUrlCreationService)
    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)
    use_case = container.resolve(CreateShortUrlUseCase)

    with pytest.raises(ShortCodeCollisionError):
        await use_case.execute(command=CreateShortUrlCommand(target_url="https://example.com"))

    assert unit_of_work_manager.rolled_back_count == 1
```

Use mirrored fake modules only for class doubles reused by multiple unit test
modules. They are allowed only under mirrored unit `capabilities`, `gateways`,
or `repositories` test packages. The fake path mirrors the production module it
replaces:

```text
src/order_service/core/orders/repositories/order_repository.py
tests/unit/core/orders/repositories/fake_order_repository.py
```

The fake module contains only class doubles and small state methods needed by
tests. It does not define fixtures, scenarios, or target factories:

```python
@dataclass(kw_only=True, slots=True)
class InMemoryOrderRepository(OrderRepository):
    """In-memory order repository double for order unit tests.

    Example:
        repository = InMemoryOrderRepository()
    """

    _orders: dict[str, OrderEntity] = field(default_factory=dict, init=False)

    async def get(self, *, order_id: str) -> OrderEntity | None:
        return self._orders.get(order_id)
```

Import the fake explicitly in the test that needs it, instantiate it as test
state, register it with the container when it replaces an injected port, then
resolve the real target:

```python
def test_lookup_uses_repository(container: Container) -> None:
    repository = InMemoryOrderRepository()
    container.add_instance(repository, provides=OrderRepository)
    service = container.resolve(OrderLookupService)
```

If every test in a module needs the same complete replacement, use a
module-local `container` fixture that depends on the parent container and
registers the replacement before returning it. Do not put double classes in
`conftest.py`.

Parameterize aggressively. When a case has more than one meaningful field, use
a small dataclass and inline the case list directly in `pytest.mark.parametrize`
unless the same case set is reused by multiple tests.

## Integration Tests

Integration tests use the real internal application graph: delivery, DI, use
cases, services, UoWs, repositories, and the database. Stub only external
systems. For SQLAlchemy projects, `tests/integration/conftest.py` owns the
transactional DB-backed `container` fixture:

```text
create migrated test database
open per-test outer transaction
bind SQLAlchemySessionFactory to that transaction
create real app container
register the transactional session factory
yield container
roll back transaction
```

Core use-case integration tests call resolved use cases directly:

```python
@pytest.mark.anyio
async def test_execute_normalizes_and_persists_task(container: Container) -> None:
    create_task_use_case = container.resolve(CreateTaskUseCase)
    list_tasks_use_case = container.resolve(ListTasksUseCase)

    created_task = await create_task_use_case.execute(
        command=CreateTaskCommand(title="  Ship skill  "),
    )
    listed_tasks = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert created_task.title == "Ship skill"
    assert listed_tasks.tasks == [created_task]
```

FastAPI route tests use a generic support helper so app construction happens
after any test-specific external-boundary override:

```python
@asynccontextmanager
async def open_test_async_client(container: Container) -> AsyncIterator[AsyncClient]:
    app_factory = container.resolve(FastAPIFactory)
    app = app_factory()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
```

Route test bodies receive `container` and open the client:

```python
from fastapi import status


@pytest.mark.anyio
async def test_create_task_route_persists_normalized_title(container: Container) -> None:
    async with open_test_async_client(container) as client:
        response = await client.post("/api/v1/tasks", json={"title": "  Ship skill  "})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "Ship skill"
```

Operational probe route tests are the explicit exception to `/api/v1` business
route paths. `/healthz` is a lightweight process probe and must not query
databases, queues, caches, network services, or external SDKs. `/readyz` checks
required infrastructure; for SQLAlchemy services this means a cheap bounded
`SELECT 1` through the health readiness gateway adapter. Probe tests assert
`Cache-Control: no-store`, `503` for readiness failure, and OpenAPI exclusion.

Do not mock internal use cases, services, or capabilities in integration tests.
Only add repository, UoW, model, session, or adapter integration tests when
they cover meaningful project-owned behavior: nontrivial mapping, query shape,
exception translation, lifecycle policy, or a regression that would not be
covered through a use case or route.

## Database Isolation

For SQLAlchemy projects:

- Run Alembic once for a session-scoped migrated SQLite database.
- For each data integration test, open one connection and an outer
  transaction.
- Bind sessions with `join_transaction_mode="create_savepoint"`.
- Roll back the outer transaction in teardown.
- For SQLite/aiosqlite, create the test engine with
  `connect_args={"autocommit": False}` so SAVEPOINT work stays inside the
  outer transaction.
- Migration tests still use fresh temp database files because DDL is the
  behavior under test.

Do not call `metadata.create_all()` or `drop_all()` in source or tests.

## Architecture Guardrails

Use the packaged architecture wrapper:

```python
from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    assert_specx_architecture,
)


def test_specx_architecture() -> None:
    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[3],
            package_name="order_service",
        )
    )
```

`SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE` is enabled by default. Disable it
only for deliberate legacy migrations.

## Avoid

- No per-target test folders.
- No `harness.py`, test factories, or target harnesses.
- No `tests/_support/fakes` package.
- No shared `tests/**/_fakes.py` files.
- No `fake_*.py` modules outside mirrored unit `capabilities`, `gateways`, or
  `repositories` test packages.
- No fake modules that do not mirror a real source module.
- No test double classes in `conftest.py`.
- No filler tests.
- No repository/UoW/model/session tests just to mirror source files.
- No tests whose real assertion is that an upstream library works.
- No tests that only assert `container.resolve(...)` returns an instance.
- No internal use-case, service, or capability mocks in integration tests.
- No legacy `/api/v1/health` endpoint for operational probing; use unversioned
  `/healthz` and `/readyz`.
- No raw integer status codes in FastAPI route assertions; use
  `fastapi.status` constants.
- No grouped mock fixtures that register several unrelated collaborators for a
  test that exercises only one of them.
- No `container.resolve(FastAPIFactory)()` inline; resolve the factory first,
  then call it.
- No framework request objects in unit tests.
- No SQLAlchemy sessions, FastAPI apps, or real IO in unit tests.
- No broad autouse fixtures that hide DB, settings, or container state.
- No global shared containers across tests.
- No placeholder tests for empty folders or future structure.
