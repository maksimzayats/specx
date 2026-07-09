# Specx Diwire Reference

Use `diwire` to keep object construction in one place and application classes
free from container access. Generated projects use `diwire` heavily in tests:
fixtures provide containers, tests register overrides directly when needed, and
targets are resolved with `container.resolve(Target)`.

## Injectable Classes

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.orders.dtos.create_order_result_dto import CreateOrderResultDTO
from order_service.core.orders.repositories.order_unit_of_work import (
    OrderUnitOfWorkManager,
)
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

Use private fields for dependencies and inherit the matching scoped Specx
foundation base. Prefer concrete project classes unless there is a real
boundary.

## Container

```python
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy


def get_container() -> Container:
    container = Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
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

Do not register SQLAlchemy repositories that require an active session directly
in the runtime container. Create those repositories inside the active UoW, or
resolve them in tests only after registering an active test session.

## FastAPI Composition

Resolve the outer app factory only. Resolve first, then call:

```python
from order_service.delivery.fastapi.factory import FastAPIFactory
from order_service.ioc.container import get_container

container = get_container()
app_factory = container.resolve(FastAPIFactory)
app = app_factory()
```

The factory receives controllers through `Injected[...]`. Controllers receive
use cases through `Injected[...]`.

## Pytest Containers

Use native pytest fixtures that return explicit containers. Do not enable
`diwire.integrations.pytest_plugin`, and do not use `Injected[...]` parameters
in test functions.

Unit tests start from a fresh bare container:

```python
@pytest.fixture
def container() -> Container:
    return Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
```

Tests register overrides directly before resolving the target:

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
    pricing_gateway.price = AsyncMock(side_effect=PricingUnavailableError)
    container.add_instance(pricing_gateway, provides=PricingGateway)
    use_case = container.resolve(CreateOrderUseCase)

    with pytest.raises(PricingUnavailableError):
        await use_case.execute(command=CreateOrderCommand(sku="SKU-1"))
```

Class-based doubles live in the `test_*.py` module that uses them. Do not put
test doubles in `conftest.py`, `_support`, or shared `_fakes.py` files.

## Test Overrides

Use overrides in unit tests and for external-boundary stubs. FastAPI
integration tests should resolve the real internal graph and use a
transactional database-backed container.

For FastAPI route tests, keep app construction after any test-specific
external-boundary override by using a generic helper:

```python
@asynccontextmanager
async def open_test_async_client(container: Container) -> AsyncIterator[AsyncClient]:
    app_factory = container.resolve(FastAPIFactory)
    app = app_factory()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
```

For integration tests that replace persistence failure behavior, register the
replacement session factory before resolving use cases, repositories, UoWs,
controllers, or `FastAPIFactory`.

## Do Not

- Do not pass `Container` into a use case, service, controller, or adapter.
- Do not resolve dependencies from inside core.
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
