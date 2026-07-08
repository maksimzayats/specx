# Specx Diwire Reference

Use `diwire` to keep object construction in one place and application classes
free from container access. Generated projects should use `diwire` heavily in
tests as well: fixtures configure overrides, then tests receive resolved
components.

## Injectable Classes

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.orders.dtos.create_order_result_dto import CreateOrderResultDTO
from order_service.core.orders.repositories.order_unit_of_work import (
    OrderUnitOfWorkManager,
)
from specx.foundation.command import BaseCommand
from specx.foundation.use_case import BaseUseCase


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

Use private fields for dependencies and inherit the matching `specx.foundation`
base. Prefer concrete project classes unless there is a real boundary.

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

## Pytest Fixtures

Use native pytest fixtures that return explicit containers. Do not enable
`diwire.integrations.pytest_plugin`, and do not use `Injected[...]` parameters
in test functions.

```python
@pytest.fixture
def container() -> Container:
    container = get_container()
    repository = InMemoryOrderRepository()
    unit_of_work_manager = InMemoryOrderUnitOfWorkManager(repository=repository)
    container.add_instance(repository, provides=InMemoryOrderRepository)
    container.add_instance(unit_of_work_manager, provides=OrderUnitOfWorkManager)
    return container
```

Tests receive resolved components through fixtures:

```python
@pytest.fixture
def create_order_use_case(container: Container) -> CreateOrderUseCase:
    return container.resolve(CreateOrderUseCase)
```

## Test Overrides

Use overrides in unit tests and for external-boundary stubs. FastAPI
integration tests should resolve the real internal graph and use a
transactional database-backed container.

```python
@pytest.fixture
def order_summary_gateway(container: Container) -> FakeOrderSummaryGateway:
    gateway = FakeOrderSummaryGateway()
    container.add_instance(gateway, provides=OrderSummaryGateway)
    return gateway
```

```python
from fastapi import status


async def test_create_order_route_persists_order(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.post("/api/v1/orders", json={"sku": "SKU-1"})

    assert response.status_code == status.HTTP_201_CREATED
```

For integration tests that replace persistence, register the replacement
session factory before resolving use cases, repositories, UoWs, controllers, or
`FastAPIFactory`.

## Do Not

- Do not pass `Container` into a use case, service, controller, or adapter.
- Do not resolve dependencies from inside core.
- Do not instantiate use cases, services, controllers, repositories, or UoW
  managers by hand in test bodies.
- Do not hide manual production graph assembly in test factory classes.
- Do not mock internal use cases or services in integration tests.
- Do not add tests that only assert `container.resolve(...)` returns an
  instance. Container-focused tests must prove a real binding, lifecycle rule,
  or application behavior.
- Do not add DI or adapter tests merely to mirror source files or prove
  upstream library behavior.
- Do not bundle unrelated mocks in one fixture. Register one override fixture
  per collaborator unless the subject genuinely consumes a collection.
- Do not register every concrete class manually.
- Do not instantiate injected collaborators inside use cases or services.
- Do not inject an active UoW instance or `Provider[UnitOfWork]` into a
  long-lived use case. Inject the scope `UnitOfWorkManager`; the manager opens
  and closes active UoW objects inside each use-case execution.
