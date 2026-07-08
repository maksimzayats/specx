# Specx Infrastructure Adapter Reference

Infrastructure adapters perform technical IO for core repository and gateway
contracts.

## Core Port

```python
from abc import abstractmethod

from specx.foundation.repository import BaseRepository


class UserDirectoryRepository(BaseRepository):
    """Repository port for user-directory email lookups.

    Example:
        email = await repository.find_email(user_id="user-1")
    """

    @abstractmethod
    async def find_email(self, *, user_id: str) -> str | None:
        raise NotImplementedError
```

Define repositories in `core/<scope>/repositories/` for owned persistence.
Define gateways in `core/<scope>/gateways/` for outbound business capabilities
provided by external systems.

## Core Gateway Port

```python
from order_service.core.tasks.dtos.task_summary_dto import TaskSummaryDTO
from specx.foundation.gateway import BaseGateway


class TaskSummaryGateway(BaseGateway):
    """Gateway that generates task summaries.

    External effect: calls a configured text-generation provider.

    Example:
        summary = await gateway.generate_summary(description="Ship the skill")
    """

    async def generate_summary(self, *, description: str) -> TaskSummaryDTO:
        raise NotImplementedError
```

Gateway ports expose business capabilities, not provider mechanics. Avoid names
such as `OpenAIClientGateway` for the core port. Use
`TaskSummaryGateway.generate_summary(...)`, not `post_chat_completion(...)`.
Gateway methods must not return entities, ORM models, SDK responses, or raw HTTP
responses.

## HTTP Or SDK Gateway Adapter

Inject a network client or a project-owned client factory. Do not instantiate
`httpx.AsyncClient` directly inside `find_*`, `send_*`, or other adapter
business methods.

Factory:

```python
from dataclasses import dataclass

import httpx

from specx.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class AsyncHttpClientFactory(BaseFactory):
    """Factory for creating bounded-lifetime async HTTP clients.

    Example:
        async with factory(timeout_seconds=5.0) as client:
            response = await client.get("https://example.invalid")
    """

    def __call__(self, *, timeout_seconds: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout_seconds)
```

Adapter:

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.users.repositories.user_directory_repository import (
    UserDirectoryRepository,
)
from order_service.core.users.infrastructure.http.client_factory import (
    AsyncHttpClientFactory,
)
from order_service.core.users.infrastructure.http.settings import UserDirectorySettings


@dataclass(kw_only=True, slots=True)
class HttpUserDirectoryRepository(UserDirectoryRepository):
    """HTTP adapter for user-directory email lookups.

    Example:
        email = await repository.find_email(user_id="user-1")
    """

    _client_factory: Injected[AsyncHttpClientFactory]
    _settings: Injected[UserDirectorySettings]

    async def find_email(self, *, user_id: str) -> str | None:
        async with self._client_factory(
            timeout_seconds=self._settings.timeout_seconds,
        ) as client:
            response = await client.get(f"{self._settings.base_url}/users/{user_id}")

        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return str(payload["email"])
```

Settings can live near the adapter if only that adapter consumes them.

If the app needs a long-lived shared client, create and dispose it in an
delivery app lifespan or factory, add it to the container as an instance, and
inject that instance into the adapter. Keep lifecycle ownership outside core.

OpenAI-style gateway implementation:

```python
from dataclasses import dataclass

from diwire import Injected
from openai import AsyncOpenAI

from order_service.core.tasks.dtos.task_summary_dto import TaskSummaryDTO
from order_service.core.tasks.gateways.task_summary_gateway import TaskSummaryGateway
from order_service.core.tasks.infrastructure.openai.settings import OpenAISettings


@dataclass(kw_only=True, slots=True)
class OpenAITaskSummaryGateway(TaskSummaryGateway):
    """OpenAI adapter for task summary generation.

    External effect: calls the OpenAI API.

    Example:
        summary = await gateway.generate_summary(description="Ship the skill")
    """

    _client: Injected[AsyncOpenAI]
    _settings: Injected[OpenAISettings]

    async def generate_summary(self, *, description: str) -> TaskSummaryDTO:
        response = await self._client.responses.create(
            model=self._settings.summary_model,
            input=f"Summarize this task: {description}",
        )
        return TaskSummaryDTO(text=response.output_text)
```

Concrete gateway implementations live under
`core/<scope>/infrastructure/<technology>/` and inherit the scope gateway port,
not `BaseGateway` directly.

## SQLAlchemy Repository

Use `$specx-sqlalchemy-migrations` when adding SQLAlchemy models or repository
adapters. App-wide SQLAlchemy settings and session factories live under
top-level `infrastructure/sqlalchemy/`; scope-owned models, mappers,
repositories, and unit-of-work adapters live under
`core/<scope>/infrastructure/sqlalchemy/`.

```python
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.core.orders.entities.order_entity import OrderEntity
from order_service.core.orders.repositories.order_repository import OrderRepository
from order_service.core.orders.infrastructure.sqlalchemy.models.order import OrderModel


@dataclass(kw_only=True, slots=True)
class SQLAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy adapter for order persistence.

    Example:
        order = await repository.get(order_id=1)
    """

    _session: AsyncSession

    async def get(self, *, order_id: int) -> OrderEntity | None:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.id == order_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return OrderEntity(id=model.id, total=model.total)
```

Repositories may flush. UoW owns commit, rollback, session close, and
transaction begin.

`AsyncSession`, Redis clients, SDK clients, and network clients are adapter
dependencies. Receive them through constructor arguments or injected factories;
do not create them inside core use cases or services.

Do not call `Base.metadata.create_all`, `metadata.create_all`, or `drop_all`
from application code. Schema changes must be represented as Alembic revisions.

## Unit Of Work Port

```python
from abc import abstractmethod

from specx.foundation.unit_of_work import BaseUnitOfWork
from specx.foundation.unit_of_work_manager import BaseUnitOfWorkManager


class UnitOfWork(BaseUnitOfWork):
    """Active order transaction boundary.

    Example:
        order = await unit_of_work.orders.get(order_id=1)
    """

    @property
    @abstractmethod
    def orders(self) -> OrderRepository:
        raise NotImplementedError


class UnitOfWorkManager(BaseUnitOfWorkManager[UnitOfWork]):
    """Manager that opens active order units of work.

    Example:
        async with unit_of_work_manager as unit_of_work:
            order = await unit_of_work.orders.get(order_id=1)
    """
```

## Unit Of Work Implementation

```python
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

from diwire import Injected
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction


@dataclass(kw_only=True, slots=True)
class SQLAlchemyUnitOfWork(UnitOfWork):
    """Active SQLAlchemy transaction for order repositories.

    Example:
        order = await unit_of_work.orders.get(order_id=1)
    """

    _session: AsyncSession
    _transaction: AsyncSessionTransaction
    _orders: OrderRepository = field(init=False)
    _closed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._orders = SQLAlchemyOrderRepository(_session=self._session)

    @property
    def orders(self) -> OrderRepository:
        self._ensure_open()
        return self._orders

    async def _commit(self) -> None:
        self._ensure_open()
        await self._transaction.commit()

    async def _rollback(self) -> None:
        self._ensure_open()
        await self._transaction.rollback()

    async def _close(self) -> None:
        if self._closed:
            return
        await self._session.close()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            msg = "Unit of work is closed."
            raise RuntimeError(msg)


@dataclass(kw_only=True, slots=True)
class SQLAlchemyUnitOfWorkManager(UnitOfWorkManager):
    """SQLAlchemy manager that owns order UoW lifecycle.

    Example:
        async with manager as unit_of_work:
            order = await unit_of_work.orders.get(order_id=1)
    """

    _session_factory: Injected[SQLAlchemySessionFactory]
    _current_unit_of_work: ContextVar[SQLAlchemyUnitOfWork | None] = field(
        default_factory=lambda: ContextVar("current_order_unit_of_work", default=None),
        init=False,
    )
    _current_token: ContextVar[Token[SQLAlchemyUnitOfWork | None] | None] = field(
        default_factory=lambda: ContextVar("current_order_unit_of_work_token", default=None),
        init=False,
    )

    async def __aenter__(self) -> UnitOfWork:
        if self._current_unit_of_work.get() is not None:
            msg = "Nested order unit of work scopes are not supported."
            raise RuntimeError(msg)

        session = self._session_factory()
        try:
            transaction = await session.begin()
            unit_of_work = SQLAlchemyUnitOfWork(
                _session=session,
                _transaction=transaction,
            )
        except BaseException:
            await session.close()
            raise

        token = self._current_unit_of_work.set(unit_of_work)
        self._current_token.set(token)
        return unit_of_work

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        unit_of_work = self._current_unit_of_work.get()
        token = self._current_token.get()
        if unit_of_work is None or token is None:
            msg = "Unit of work manager is not active."
            raise RuntimeError(msg)

        try:
            try:
                if exc_type is None:
                    await unit_of_work._commit()
                else:
                    await unit_of_work._rollback()
            finally:
                await unit_of_work._close()
        finally:
            self._current_unit_of_work.reset(token)
            self._current_token.set(None)

        return False
```

The active UoW exposes repositories. The manager owns opening sessions,
beginning transactions, committing or rolling back, closing resources, and
preventing invalid nested scopes. Use cases should not call commit, rollback,
or close directly.

## Container Binding

```python
def _register_dependencies(container: Container) -> None:
    container.add(HttpUserDirectoryRepository, provides=UserDirectoryRepository)
    container.add(OpenAITaskSummaryGateway, provides=TaskSummaryGateway)
    container.add(
        SQLAlchemyUnitOfWorkManager,
        provides=UnitOfWorkManager,
    )
```

Register the UoW manager and inject that manager into use cases. Do not inject
`Provider[UnitOfWork]`; the manager is responsible for producing a fresh active
transaction for each use-case execution.

## Integration Tests

- Use real adapters against temporary databases or stub servers.
- For SQLAlchemy, run `alembic upgrade head` against the temporary database
  before exercising repositories or HTTP routes.
- Add a migration smoke test that verifies expected tables and
  `alembic_version` exist.
- Add an Alembic drift test with `alembic check` or the equivalent command API.
- Keep delivery integration tests away from SQLAlchemy models and sessions.
- Test exception translation at the adapter boundary when callers depend on it.

## Avoid

- No business decisions in adapters.
- No delivery imports.
- No framework schemas as return values.
- No raw SDK objects returned to core.
- No gateway ports under `repositories/`.
- No concrete gateway implementations outside
  `core/<scope>/infrastructure/<technology>/`.
- No entities returned from gateway methods.
- No bare adapter, repository, factory, or UoW classes.
- No schema bootstrap helper in `src/`.
