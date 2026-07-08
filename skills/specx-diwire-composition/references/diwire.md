# Specx Diwire Reference

Use `diwire` to keep object construction in one place and application classes
free from container access.

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
base.
Prefer concrete project classes unless there is a real boundary.

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

## Private Registration

Do not create a public `ioc/registry.py` for the default Specx shape. Keep
explicit bindings next to container creation in private
`_register_dependencies(...)`. Keep that function empty until an explicit
binding is needed.

Do not register SQLAlchemy repositories that require an active session directly
in the container. Create those repositories inside the active UoW. Concrete
stateless factories such as `AsyncHttpClientFactory` can usually be auto-wired
and do not need manual registration. Gateway implementations that satisfy a
core `BaseGateway` port should be registered explicitly with `provides=...`.
Register existing client instances only when their lifecycle is owned by a
delivery app or factory:

```python
import httpx


def _register_runtime_instances(container: Container, *, client: httpx.AsyncClient) -> None:
    container.add_instance(client, provides=httpx.AsyncClient)
```

## FastAPI Composition

Resolve the outer app factory only:

```python
from order_service.delivery.fastapi.factory import FastAPIFactory
from order_service.ioc.container import get_container

container = get_container()
app = container.resolve(FastAPIFactory)()
```

The factory receives controllers through `Injected[...]`. Controllers receive
use cases through `Injected[...]`.

## Test Overrides

Override dependencies before resolving the graph:

```python
def test_app_uses_fake_repository() -> None:
    container = get_container()
    container.add_instance(FakeOrderRepository(), provides=OrderRepository)

    app = container.resolve(FastAPIFactory)()
```

Direct constructor tests are fine for simple core classes:

```python
use_case = CreateOrderUseCase(
    _order_pricing_service=OrderPricingService(),
    _unit_of_work_manager=FakeOrderUnitOfWorkManager(),
)
```

## Do Not

- Do not pass `Container` into a use case, service, controller, or adapter.
- Do not resolve dependencies from inside core.
- Do not register every concrete class manually.
- Do not instantiate injected collaborators inside use cases or services.
- Do not inject an active UoW instance or `Provider[UnitOfWork]` into a
  long-lived use case. Inject the scope `UnitOfWorkManager`; the manager opens
  and closes active UoW objects inside each use-case execution.
- Do not hide external client/session construction inside core or adapter
  business methods; inject clients, session factories, or project-owned
  factories instead.
