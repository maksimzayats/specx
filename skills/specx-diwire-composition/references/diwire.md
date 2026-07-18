# specx Diwire Reference

Use `diwire` to keep object construction in one place and application classes
free from container access. Generated projects use `diwire` heavily in tests:
fixtures provide containers, tests register overrides directly when needed, and
targets are resolved with `container.resolve(Target)`.

## Contents

- [Injectable classes](#injectable-classes)
- [Container](#container)
- [FastAPI composition](#fastapi-composition)
- [Pytest containers](#pytest-containers)
- [Test overrides](#test-overrides)
- [Do not](#do-not)

## Injectable Classes

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.orders.dtos.create_order_result_dto import CreateOrderResultDTO
from order_service.core.orders.repositories.order_unit_of_work import (
    OrderUnitOfWorkManager,
)
from order_service.core.orders.services.order_pricing_service import OrderPricingService
from specx.core.foundation.command import BaseCommand
from specx.core.foundation.use_case import BaseUseCase


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateOrderCommand(BaseCommand):
    """Command for creating an order.

    Example:
        CreateOrderCommand(sku="SKU-1")
    """

    sku: str


@dataclass(kw_only=True, slots=True)
class CreateOrderUseCase(BaseUseCase):
    """Use case that creates an order through an order UoW manager.

    Example:
        result = await use_case.execute(command=CreateOrderCommand(sku="SKU-1"))
    """

    _order_pricing_service: Injected[OrderPricingService]
    _unit_of_work_manager: Injected[OrderUnitOfWorkManager]

    async def execute(self, *, command: CreateOrderCommand) -> CreateOrderResultDTO:
        async with self._unit_of_work_manager as uow:
            order = await uow.orders.create(sku=command.sku)
            return CreateOrderResultDTO(order_id=order.id)
```

Python awaits the unit of work's `__aexit__` before completing this return, so
the DTO reaches the caller only after commit and cleanup succeed.

Use private fields for dependencies and inherit the matching scoped specx
foundation base. Prefer concrete project classes unless there is a real
boundary. Keep this injection constructor-based; specx application code does
not use `resolver_context.inject` function wrappers. DIWire's mypy plugin only
refines those wrappers, so constructor-field injection does not require the
plugin.

## Container

```python
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy


def get_container() -> Container:
    container = Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
    container.add_instance(container, provides=Container)
    _register_dependencies(container)

    return container


def _register_dependencies(container: Container) -> None:
    container.add(SQLAlchemyReadinessCheckGateway, provides=ReadinessCheckGateway)
    container.add(OpenAITaskSummaryGateway, provides=TaskSummaryGateway)
    container.add(
        SQLAlchemyOrderUnitOfWorkManager,
        provides=OrderUnitOfWorkManager,
    )
```

DIWire recognizes `pydantic-settings` subclasses and auto-registers them as
zero-argument, root-scoped singleton factories. Let it resolve
`BaseRuntimeSettings` subclasses normally. Register a prebuilt settings instance
only for an intentional override, and do so before resolving its consumer:

```python
settings = UserDirectorySettings.model_validate(
    {"base_url": "https://example.test"},
)
container.add_instance(settings, provides=UserDirectorySettings)
```

Runtime settings belong at delivery, infrastructure, and composition edges.
Core use cases and services receive typed core policies or capabilities, not
`BaseRuntimeSettings` subclasses.

Do not register SQLAlchemy repositories that require an active session directly
in the runtime container. Create those repositories inside the active UoW, or
resolve them in tests only after registering an active test session.

Register the container instance only for `FastAPILifecycle`. Do not inject it
into controllers, use cases, services, adapters, or factories.

## FastAPI Composition

Configure runtime logging before composing the app, then resolve the outer app
factory. Resolve first, then call:

```python
from order_service.delivery.fastapi.factory import FastAPIFactory
from order_service.infrastructure.logging.configurator import LoggingConfigurator
from order_service.ioc.container import get_container

container = get_container()
logging_configurator = container.resolve(LoggingConfigurator)
logging_configurator.configure()

app_factory = container.resolve(FastAPIFactory)
app = app_factory()
```

The factory receives `FastAPILifecycle` and controllers through
`Injected[...]`. Controllers receive use cases through `Injected[...]`.
`FastAPILifecycle` is the only generated class that may inject
`diwire.Container`, and only to call `container.aclose()` on shutdown after
closing app-owned resources.

Do not inject `logging.Logger`, register `logging.Logger`, or build logger
providers in the container. Runtime logging setup is a configurator concern.
Classes that emit logs should call `logging.getLogger(...)` locally in
`__post_init__`.

## Pytest Containers

Use native pytest fixtures that return explicit containers. Do not enable
`diwire.integrations.pytest_plugin`, and do not use `Injected[...]` parameters
in test functions.

Unit tests start from a fresh application container built by the real
composition root:

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

Add an override to this fixture when it applies to the whole test suite. Tests
register scenario-specific overrides directly before resolving the target:

```python
@pytest.mark.anyio
async def test_create_order_with_selected_price(container: Container) -> None:
    pricing_gateway = FakePricingGateway(price=100)
    container.add_instance(pricing_gateway, provides=PricingGateway)
    use_case = container.resolve(CreateOrderUseCase)

    result = await use_case.execute(command=CreateOrderCommand(sku="SKU-1"))

    assert result.total == 100
```

When only one behavior changes, create the mock inline in the test:

```python
@pytest.mark.anyio
async def test_create_order_propagates_pricing_error(container: Container) -> None:
    pricing_gateway = MagicMock(spec=PricingGateway)
    pricing_gateway.price = AsyncMock(side_effect=PricingUnavailableError())
    container.add_instance(pricing_gateway, provides=PricingGateway)
    use_case = container.resolve(CreateOrderUseCase)

    with pytest.raises(PricingUnavailableError):
        await use_case.execute(command=CreateOrderCommand(sku="SKU-1"))
```

One-off class-based doubles live in the `test_*.py` module that uses them.
When a double is reused by multiple unit test modules, put it in a mirrored
`tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
module. Do not put test doubles in `conftest.py`, `_support`, shared
`_fakes.py` files, or fake modules outside those mirrored unit
port/capability packages.

## Test Overrides

Use overrides in unit tests and for external-boundary stubs. FastAPI
integration tests should resolve the real internal graph and use a
transactional database-backed container.

For FastAPI route tests, keep app construction after any test-specific
external-boundary override by using a generic helper:

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

Use `asgi-lifespan` for the helper because HTTPX2 ASGI transports do not trigger
application lifespan by themselves. `manager.app` is the state-aware ASGI app;
using the original app loses state yielded by the lifespan context.

For integration tests that replace persistence failure behavior, register the
replacement session factory before resolving use cases, repositories, UoWs,
controllers, or `FastAPIFactory`.

## Do Not

- Do not pass `Container` into a use case, service, controller, adapter, or
  factory. The only exception is `FastAPILifecycle`, which receives it for
  shutdown cleanup.
- Do not inject `logging.Logger` or register it as a dependency. Use local
  stdlib class loggers for classes that actually log.
- Do not resolve dependencies from inside core.
- Do not inject runtime settings into core use cases, services, capabilities,
  entities, repositories, or gateway ports. Map genuine business configuration
  to typed core collaborators at composition.
- Do not use `resolver_context.inject` to hide resolution in application
  functions; keep project dependencies in constructor fields.
- Do not instantiate project use cases, services, controllers, repositories, or
  UoW managers by hand in tests; resolve project classes from `container`.
- Do not hide manual production graph assembly in test helper classes.
- Do not create target test factories or harnesses.
- Do not mock internal use cases, services, or capabilities in integration
  tests.
- Do not add tests that only assert `container.resolve(...)` returns an
  instance. Container-focused tests must prove a real binding, lifecycle rule,
  or application behavior.
- Do not add DI or adapter tests merely to mirror source files or prove
  upstream library behavior.
- Do not bundle unrelated mocks in one fixture. Register one override fixture
  per collaborator unless the subject genuinely consumes a collection.
- Do not register every concrete class manually.
- Do not instantiate injected collaborators inside use cases or services.
- Do not inject repositories, active UoW instances, `Provider[UnitOfWork]`,
  SQLAlchemy sessions, engines, session factories, or concrete infrastructure
  adapters into a long-lived use case. Inject the scope `UnitOfWorkManager`;
  the manager opens and closes active UoW objects inside each use-case
  execution.
