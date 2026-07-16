# Specx Testing Reference

Tests prove behavior and protect boundaries while `diwire` assembles project
graphs through native pytest fixtures. Core test bodies receive `container`,
register scenario-specific overrides directly, resolve the target class, then
exercise behavior.

## Contents

- [Layout](#layout)
- [Unit tests](#unit-tests)
- [Async backends](#async-backends)
- [Integration tests](#integration-tests)
- [Database isolation](#database-isolation)
- [Architecture guardrails](#architecture-guardrails)
- [Avoid](#avoid)

## Layout

Mirror source paths under the test layer that owns the behavior:

```text
tests/
  conftest.py
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

Top-level logging infrastructure is a narrow exception when it has real
configuration behavior: unit-test `LoggingConfigurator` by overriding
`LoggingSettings`, monkeypatching `logging.config.dictConfig`, and asserting
the generated stdlib logging config. Use `caplog` only when a log record
protects meaningful project behavior; do not add log assertions just because a
logger field exists.

FastAPI lifecycle code is another narrow delivery exception when it owns real
resource cleanup. Unit-test `FastAPILifecycle` by overriding closeable
infrastructure resources and asserting shutdown order. Do not test lifecycle
only to prove FastAPI's own lifespan implementation.

## Unit Tests

Unit tests use a fresh application container from the real composition root:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from order_service.ioc.container import get_container

if TYPE_CHECKING:
    from diwire import Container


@pytest.fixture
def container() -> Container:
    return get_container()
```

Put project-wide test overrides in this fixture. Resolve project classes from
the container, registering scenario-specific overrides before resolving the
target:

```python
from dataclasses import dataclass
from decimal import Decimal

from diwire import Container

from order_service.core.orders.capabilities.tax_rate_capability import TaxRateCapability
from order_service.core.orders.services.order_pricing_service import OrderPricingService


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

Use inline mocks when a scenario only needs one collaborator behavior changed.
Prefer `create_autospec(..., instance=True, spec_set=True)` so the mock enforces
the collaborator API and creates `AsyncMock` methods for async functions:

```python
from unittest.mock import create_autospec


@pytest.mark.anyio
async def test_execute_rolls_back_when_creation_fails(container: Container) -> None:
    creation_service = create_autospec(
        ShortUrlCreationService,
        instance=True,
        spec_set=True,
    )
    creation_service.create.side_effect = ShortCodeCollisionError(max_attempts=5)
    unit_of_work_manager = TrackingShortUrlUnitOfWorkManager()

    container.add_instance(creation_service, provides=ShortUrlCreationService)
    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)
    use_case = container.resolve(CreateShortUrlUseCase)

    with pytest.raises(ShortCodeCollisionError):
        await use_case.execute(command=CreateShortUrlCommand(target_url="https://example.com"))

    creation_service.create.assert_awaited_once()
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

Parameterize cases that exercise the same behavior and assertion shape; keep
materially different scenarios as separately named tests. When a case has more
than one meaningful field, use a small dataclass and readable `pytest.param`
IDs. Remember that pytest passes mutable parameter values as-is rather than
copying them between cases.

## Async Backends

`@pytest.mark.anyio` uses AnyIO's built-in pytest plugin. Its default
`anyio_backend` fixture runs each async test on every installed supported
backend. Generated FastAPI and async-SQLAlchemy graphs are normally
asyncio-specific, so pin that fact explicitly in top-level
`tests/conftest.py`:

```python
import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

Do not pin the fixture when the project intentionally promises both asyncio
and Trio support; in that case keep every dependency backend-neutral and let
the default matrix run. Give a custom backend fixture scope at least as broad
as the widest async fixture that depends on it.

## Integration Tests

Integration tests use the real internal application graph: delivery, DI, use
cases, services, UoWs, repositories, and the database. Stub only external
systems. For SQLAlchemy projects, `tests/integration/conftest.py` owns the
transactional DB-backed `container` fixture. Prefer the production database
family whenever dialect behavior, constraints, locking, or query semantics
matter; do not silently substitute SQLite for PostgreSQL or MySQL:

```text
create migrated test database
open per-test outer transaction
bind SQLAlchemySessionFactory to that transaction
create real app container
register the transactional session factory
yield container
close container-owned resources
roll back transaction
```

Fixture teardown closes the container before rolling back and closing the
connection it depends on. This matters for direct core integration tests,
which do not enter FastAPI lifespan and therefore cannot rely on app shutdown
to call `container.aclose()`.

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
after any test-specific external-boundary override. Generated projects use the
maintained `httpx2>=2.5.0` package rather than legacy `httpx`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from asgi_lifespan import LifespanManager
from diwire import Container
from httpx2 import ASGITransport, AsyncClient

from order_service.delivery.fastapi.factory import FastAPIFactory


@asynccontextmanager
async def open_test_async_client(container: Container) -> AsyncIterator[AsyncClient]:
    app_factory = container.resolve(FastAPIFactory)
    app = app_factory()

    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
```

Use `asgi-lifespan` in this helper because HTTPX2 ASGI transports do not trigger
application lifespan by themselves. Pass `manager.app`, not the original app,
so lifespan-provided state is present in request scopes.

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

- Provision an isolated migrated test database with Alembic. A session-scoped
  database must be unique per parallel test worker.
- For each data integration test, open one connection and an outer
  transaction.
- Bind sessions with `join_transaction_mode="create_savepoint"`.
- Roll back the outer transaction in teardown.
- Use this savepoint recipe only when the database and driver have correct
  SAVEPOINT support.
- Tests for commit visibility, transaction isolation, locks, concurrency, or
  after-commit behavior use a separately isolated database and real commits;
  an enclosing rollback transaction would hide the behavior under test.
- Migration tests use a fresh isolated database or schema because DDL is the
  behavior under test. A fresh temp file is appropriate when SQLite is the
  target database.

SQLite's legacy transaction mode does not correctly enclose every SAVEPOINT.
On Python 3.12+, set `connect_args={"autocommit": False}` for both `sqlite3`
and `aiosqlite`. For Python 3.11 compatibility, or one setup that spans Python
versions, follow SQLAlchemy's event-hook recipe: disable the driver's implicit
`BEGIN` with `isolation_level = None` on connect and emit `BEGIN` from the
SQLAlchemy `begin` event (attach async-engine listeners to
`engine.sync_engine`). Do not pass the `autocommit` connection argument on
Python 3.11, where `sqlite3.Connection.autocommit` does not exist.

Do not call `metadata.create_all()` or `drop_all()` in source or tests.

## Architecture Guardrails

Run packaged framework-neutral architecture rules from the project root:

```bash
uv run --locked specx check
```

Generated projects explicitly select every applicable built-in rule:

```toml
[tool.specx]
select = ["ALL"]
```

The `ALL` selector skips rule families whose required project surface is
absent. Projects that use a narrower `select` add technology families with
`extend-select`.

Projects with a narrower base selection opt into FastAPI rules explicitly:

```toml
[tool.specx]
select = ["neutral"]
extend-select = ["fastapi"]
```

Use the typed wrapper only when a project needs programmatic custom rules:

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
            extend_select=frozenset({"fastapi"}),
        )
    )
```

`SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE` is enabled by default. Disable it
only for deliberate legacy migrations, and put a concise reason beside its
exact semantic ID in `[tool.specx].ignore`. Prefer `[tool.specx].exclude` for
generated or vendored trees that are outside the project's ownership. The
programmatic `disabled_rules` and `path_exclusions` fields remain available to
wrapper-based custom checks.

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
- No SQLAlchemy sessions, FastAPI apps, or real IO in unit tests, except a
  minimal `FastAPI()` instance in lifecycle unit tests.
- No route integration tests that bypass FastAPI lifespan.
- No legacy `httpx` imports in generated projects; use `httpx2`.
- No use of the original ASGI app when a `LifespanManager` supplies
  `manager.app`.
- No accidental AnyIO backend matrix for an asyncio-only application graph.
- No SQLite substitute when production-dialect behavior is part of the test.
- No broad autouse fixtures that hide DB, settings, or container state.
- No global shared containers across tests.
- No placeholder tests for empty folders or future structure.
