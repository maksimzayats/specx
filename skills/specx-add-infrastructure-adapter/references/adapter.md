# specx Infrastructure Adapter Reference

Infrastructure adapters perform technical IO for core repository and gateway
contracts.

## Contents

- [Core ports](#core-port)
- [HTTP or SDK adapters](#http-or-sdk-gateway-adapter)
- [SQLAlchemy repositories and sessions](#sqlalchemy-repository)
- [Logging and app resources](#logging-configurator)
- [Readiness adapters](#readiness-gateway-adapter)
- [Unit of work](#unit-of-work-port)
- [Redis, queue, and file adapters](#redis-queue-and-file-adapters)
- [Container bindings](#container-binding)
- [Integration tests](#integration-tests)
- [Avoid](#avoid)

## Core Port

```python
from abc import abstractmethod

from specx.core.foundation.repository import BaseRepository

from order_service.core.users.entities.user_entity import UserEntity


class UserRepository(BaseRepository):
    """Repository port for user persistence owned by this service.

    Example:
        user = await repository.get(user_id="user-1")
    """

    @abstractmethod
    async def get(self, *, user_id: str) -> UserEntity | None:
        raise NotImplementedError
```

Define repositories in `core/<scope>/repositories/` for owned persistence.
Define gateways in `core/<scope>/gateways/` for outbound business capabilities
provided by external systems.

## Core Gateway Port

```python
from abc import abstractmethod

from specx.core.foundation.gateway import BaseGateway

from order_service.core.tasks.dtos.task_summary_dto import TaskSummaryDTO


class TaskSummaryGateway(BaseGateway):
    """Gateway that generates task summaries.

    External effect: calls a configured text-generation provider.

    Example:
        summary = await gateway.generate_summary(description="Ship the skill")
    """

    @abstractmethod
    async def generate_summary(self, *, description: str) -> TaskSummaryDTO:
        raise NotImplementedError
```

Gateway ports expose business capabilities, not provider mechanics. Avoid names
such as `OpenAIClientGateway` for the core port. Use
`TaskSummaryGateway.generate_summary(...)`, not `post_chat_completion(...)`.
Gateway methods must not return entities, ORM models, SDK responses, or raw HTTP
responses.

`BaseGateway`, `BaseRepository`, and `BaseUnitOfWork` are ABC-backed foundation
bases. Put `@abstractmethod` on required port methods and properties so missing
DI bindings cannot recursively instantiate an unimplemented port.

## HTTP Or SDK Gateway Adapter

Inject a network client or a project-owned client factory. Generated projects
use the maintained `httpx2>=2.5.0` package and import its API from `httpx2`.
Do not instantiate `httpx2.AsyncClient` directly inside `find_*`, `send_*`, or
other adapter business methods.

Factory:

```python
from dataclasses import dataclass

import httpx2
from specx.core.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class AsyncHttpClientFactory(BaseFactory):
    """Factory for creating bounded-lifetime async HTTP clients.

    Example:
        async with factory(
            base_url="https://example.invalid",
            timeout_seconds=5.0,
        ) as client:
            response = await client.get("users/user-1")
    """

    def __call__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
    ) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(
            base_url=base_url,
            timeout=httpx2.Timeout(timeout_seconds),
        )
```

Adapter:

```python
from dataclasses import dataclass

import httpx2
from diwire import Injected

from order_service.core.users.exceptions.user_directory_response_error import (
    UserDirectoryResponseError,
)
from order_service.core.users.exceptions.user_directory_unavailable_error import (
    UserDirectoryUnavailableError,
)
from order_service.core.users.gateways.user_directory_gateway import (
    UserDirectoryGateway,
)
from order_service.core.users.infrastructure.http.client_factory import (
    AsyncHttpClientFactory,
)
from order_service.core.users.infrastructure.http.settings import UserDirectorySettings


@dataclass(kw_only=True, slots=True)
class HttpUserDirectoryGateway(UserDirectoryGateway):
    """HTTP adapter for user-directory email lookups.

    External effect: calls the user-directory HTTP API.

    Example:
        email = await gateway.find_email(user_id="user-1")
    """

    _client_factory: Injected[AsyncHttpClientFactory]
    _settings: Injected[UserDirectorySettings]

    async def find_email(self, *, user_id: str) -> str | None:
        try:
            async with self._client_factory(
                base_url=str(self._settings.base_url),
                timeout_seconds=self._settings.timeout_seconds,
            ) as client:
                response = await client.get("users", params={"user_id": user_id})

            if response.status_code == 404:
                return None
            response.raise_for_status()
        except httpx2.HTTPError as exception:
            raise UserDirectoryUnavailableError from exception

        try:
            payload = response.json()
        except ValueError as exception:
            raise UserDirectoryResponseError from exception

        email = payload.get("email") if isinstance(payload, dict) else None
        if not isinstance(email, str):
            raise UserDirectoryResponseError

        return email
```

Settings can live near the adapter if only that adapter consumes them.

Putting the validated base URL on `AsyncClient` avoids manual URL joining and
the double slash produced when a Pydantic `AnyHttpUrl` string already ends in
`/`. Percent-encode untrusted path segments, keep TLS verification enabled,
and validate external payloads before mapping them to core values. Prefer the
client's `params=` API for query values. If the remote contract requires a path
segment, accept a validated identifier value and encode it deliberately; do not
concatenate an arbitrary string into a URL.

The bounded factory above is appropriate for deliberately low-volume calls.
For recurring traffic, prefer one app-owned `AsyncClient` so connection pooling
is reused. Put that long-lived client factory or wrapper under top-level
`infrastructure/http/` even when only one scope currently consumes it; the
scope adapter imports and injects the owner, while `FastAPILifecycle` closes it
once with `await client.aclose()`. A bounded, short-lived factory may stay next
to its one scope adapter. Never create a client in a hot loop. Retry only
operations whose idempotency and total timeout budget are explicit.

For a pooled SDK, put the app-owned client factory and its settings under
top-level `infrastructure/openai/`:

```python
from dataclasses import dataclass, field

from diwire import Injected
from openai import AsyncOpenAI
from specx.core.foundation.factory import BaseFactory

from order_service.infrastructure.openai.settings import OpenAISettings


@dataclass(kw_only=True, slots=True)
class OpenAIClientFactory(BaseFactory):
    """Factory that owns the application's pooled OpenAI client.

    Example:
        client = factory()
    """

    _settings: Injected[OpenAISettings]
    _client: AsyncOpenAI = field(init=False, repr=False)
    _closed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=self._settings.api_key.get_secret_value(),
        )

    def __call__(self) -> AsyncOpenAI:
        if self._closed:
            msg = "OpenAI client factory is closed."
            raise RuntimeError(msg)
        return self._client

    async def close(self) -> None:
        if self._closed:
            return
        await self._client.close()
        self._closed = True
```

The scope-owned gateway injects that top-level owner:

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.tasks.dtos.task_summary_dto import TaskSummaryDTO
from order_service.core.tasks.gateways.task_summary_gateway import TaskSummaryGateway
from order_service.core.tasks.infrastructure.openai.settings import TaskSummarySettings
from order_service.infrastructure.openai.client_factory import OpenAIClientFactory


@dataclass(kw_only=True, slots=True)
class OpenAITaskSummaryGateway(TaskSummaryGateway):
    """OpenAI adapter for task summary generation.

    External effect: calls the OpenAI API.

    Example:
        summary = await gateway.generate_summary(description="Ship the skill")
    """

    _client_factory: Injected[OpenAIClientFactory]
    _settings: Injected[TaskSummarySettings]

    async def generate_summary(self, *, description: str) -> TaskSummaryDTO:
        client = self._client_factory()
        response = await client.responses.create(
            model=self._settings.model,
            instructions="Summarize the task in one concise sentence.",
            input=description,
        )
        return TaskSummaryDTO(text=response.output_text)
```

Concrete gateway implementations live under
`core/<scope>/infrastructure/<technology>/` and inherit the scope gateway port,
not `BaseGateway` directly.

Keep application instructions separate from untrusted input when an SDK
supports distinct fields. Treat empty, refused, malformed, or otherwise
contract-breaking provider output as an adapter failure. The SDK client is an
app-owned closeable resource; API keys stay in the factory's secret-aware
settings and must not appear in DTOs, exception text, or logs. The configurable
model name stays in the scope adapter's `TaskSummarySettings`; it does not
belong in the shared client owner.

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
from order_service.core.orders.infrastructure.sqlalchemy.models.order import OrderModel
from order_service.core.orders.repositories.order_repository import OrderRepository


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

## SQLAlchemy Session Factory

Create one app-scoped async engine and session maker under top-level
`infrastructure/sqlalchemy/`. Each UoW call receives a fresh `AsyncSession`;
an `AsyncSession` must never be shared by concurrent tasks.

```python
from dataclasses import dataclass, field

from diwire import Injected
from specx.core.foundation.factory import BaseFactory
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from order_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class SQLAlchemySessionFactory(BaseFactory):
    """Factory for fresh async sessions backed by one application engine.

    Example:
        session = session_factory()
    """

    _settings: Injected[DatabaseSettings]
    _engine: AsyncEngine = field(init=False, repr=False)
    _session_maker: async_sessionmaker[AsyncSession] = field(init=False, repr=False)
    _closed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._engine = create_async_engine(
            self._settings.url.get_secret_value(),
            pool_pre_ping=True,
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    def __call__(self) -> AsyncSession:
        if self._closed:
            msg = "SQLAlchemy session factory is closed."
            raise RuntimeError(msg)
        return self._session_maker()

    async def close(self) -> None:
        if self._closed:
            return
        await self._engine.dispose()
        self._closed = True
```

This example assumes `DatabaseSettings.url` is a Pydantic `SecretStr` with
`env_prefix="DATABASE_"`, so the environment variable is `DATABASE_URL`.
Unwrap it only where the engine is created. Keep pool sizes,
connect timeouts, and other dialect-specific options in settings consumed by
this factory. Do not log the URL. `pool_pre_ping` detects stale pooled
connections before checkout but does not retry a transaction that fails after
it starts.

Repositories may catch an expected `sqlalchemy.exc.IntegrityError` narrowly
around `flush()`, inspect documented driver details such as a SQLSTATE or
constraint name, and translate that one invariant into a core conflict error.
Re-raise unknown integrity failures. The manager will then roll back the failed
session. Never parse an entire driver error string or expose the wrapped
statement and parameters; SQLAlchemy DBAPI exceptions can contain both.

## Logging Configurator

Runtime logging is app-wide infrastructure, not a scope-owned repository or
gateway adapter. For generated API services, create
`infrastructure/logging/configurator.py` and
`infrastructure/logging/settings.py`.

```python
import logging.config
from dataclasses import dataclass
from typing import Any

from diwire import Injected
from specx.infrastructure.foundation.configurator import BaseConfigurator

from order_service.infrastructure.logging.settings import LoggingSettings


@dataclass(kw_only=True, slots=True)
class LoggingConfigurator(BaseConfigurator):
    """Configurator that applies process-wide Python logging settings.

    Example:
        configurator.configure()
    """

    _settings: Injected[LoggingSettings]

    def configure(self) -> None:
        logging.config.dictConfig(self._build_config())

    def _build_config(self) -> dict[str, Any]:
        level = self._settings.level.value

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self._settings.message_format,
                    "datefmt": self._settings.date_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": level,
            },
        }
```

Resolve and call the configurator in the runtime entrypoint before resolving
the app factory. Do not define a core logging gateway, inject `logging.Logger`,
or register loggers in the DI container. Classes that actually emit logs create
local stdlib class loggers in `__post_init__`. Keep
`disable_existing_loggers=False`; otherwise pre-existing server, SQLAlchemy,
Alembic, and library loggers can be disabled. Do not log credentials, SQL
parameters, response bodies, or full external URLs.

## Closeable App Resources

Long-lived app-owned resources such as SQLAlchemy engines, Redis pools, queue
clients, and SDK clients should expose an explicit async `close()` method on
their top-level infrastructure factory or client wrapper. `FastAPILifecycle`
calls those close methods during shutdown and then calls `container.aclose()`.
Do not close app-wide resources in controllers, core use cases, core services,
or individual request handlers.

For SQLAlchemy session factories, `close()` should await `AsyncEngine.dispose()`
and be idempotent. Construct the engine once, not once per session or request.
Use nested `finally` blocks in lifecycle so one failed close cannot prevent the
remaining resources and then `container.aclose()` from running. Do not run
Alembic migrations or `metadata.create_all()` from lifespan.

## Readiness Gateway Adapter

For `/readyz` checks of any required external dependency, define
`ReadinessCheckGateway` under
`core/health/gateways/` and implement dependency-specific checks under
`core/health/infrastructure/<technology>/`. A SQLAlchemy readiness adapter may
inject the app-wide `SQLAlchemySessionFactory`, execute a bounded `SELECT 1`,
catch low-level failures, and return a core readiness DTO such as
`HealthCheckDTO(name=HealthCheckNameEnum.DATABASE, status=HealthProbeStatusEnum.FAIL)`.
Do not put this check in a FastAPI controller or delivery service.

Use an application-side timeout such as `asyncio.timeout(...)` around session
creation and `SELECT 1`, close the session on every path, and catch
`TimeoutError` plus the narrow SQLAlchemy failure family. Readiness reports a
stable dependency name and pass/fail status only; it must not return exception
text, database hosts, URLs, pool state, or SQL. Liveness must not call this
adapter.

Do not call `Base.metadata.create_all`, `metadata.create_all`, or `drop_all`
from application code. Schema changes must be represented as Alembic revisions.

## Unit Of Work Port

```python
from abc import abstractmethod

from specx.core.foundation.unit_of_work import BaseUnitOfWork
from specx.core.foundation.unit_of_work_manager import BaseUnitOfWorkManager


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

The manager may be app-scoped and entered concurrently, so its active UoW and
token are `ContextVar` state rather than ordinary instance fields. This gives
each task a fresh session while rejecting a nested scope in the same task.
Context is copied into child tasks: do not start parallel database work inside
an active UoW or call the same `AsyncSession` concurrently. Open independent
top-level UoW scopes for independent transactions.

The setup path catches `BaseException` only to guarantee that a just-created
session is closed on cancellation or another exceptional setup failure.
Adapter business methods should catch narrow driver or SDK exceptions. Map
every ORM value needed by core while the session is open; never return an ORM
object or rely on lazy loading after UoW exit.

## Redis, Queue, And File Adapters

- A Redis adapter is a repository only when Redis owns application persistence;
  it is a gateway when Redis provides a cache, lock, stream, or external
  capability. Keep key namespaces, serialization versions, TTL policy, and
  required atomic operations explicit. Own one long-lived client or pool at the
  app edge and close it in lifecycle.
- A database transaction cannot atomically include a Redis command or queue
  publish. For persist-and-publish workflows, use a transactional outbox or an
  explicitly designed idempotency, retry, and compensation policy. Do not hold
  a database transaction open while waiting on avoidable network IO.
- Queue payloads are versioned boundary contracts, not entities or framework
  objects. Define deduplication and idempotency behavior, and acknowledge
  inbound work only after the owned state transition is durable.
- File adapters resolve untrusted names beneath a configured root, reject path
  escape, and use an atomic replace when readers must not observe partial
  writes. Move blocking filesystem calls off the event-loop thread.

## Container Binding

```python
def _register_dependencies(container: Container) -> None:
    container.add(AsyncHttpClientFactory)
    container.add(OpenAIClientFactory)
    container.add(SQLAlchemySessionFactory)
    container.add(HttpUserDirectoryGateway, provides=UserDirectoryGateway)
    container.add(OpenAITaskSummaryGateway, provides=TaskSummaryGateway)
    container.add(
        SQLAlchemyUnitOfWorkManager,
        provides=UnitOfWorkManager,
    )
```

Register the UoW manager and inject that manager into use cases. Do not inject
repositories, active UoWs, `Provider[UnitOfWork]`, SQLAlchemy sessions,
engines, session factories, or concrete infrastructure adapters into use cases.
The manager is responsible for producing a fresh active transaction for each
use-case execution.

Concrete resources such as `SQLAlchemySessionFactory` are registered once and
resolved at app scope by the standard container. Inject that same instance into
the UoW manager and `FastAPILifecycle`; do not construct a second engine merely
for shutdown. Prebuilt SDK or shared HTTP clients use an explicit instance
binding and are closed by their declared lifecycle owner.

For the factory shown above, inject the same `OpenAIClientFactory` into
`FastAPILifecycle` and call `await self._openai_client_factory.close()` in its
nested shutdown `finally` chain before `container.aclose()`. Do not construct a
second `AsyncOpenAI`, and do not assume `container.add(...)` closes an SDK
client that the application created.

## Integration Tests

- Add adapter integration tests only when they cover project-owned behavior:
  nontrivial mapping, query shape, exception translation, lifecycle policy, or
  a regression that is not already covered through a use case or route.
- Use real adapters against temporary databases or stub servers only for those
  meaningful cases.
- For SQLAlchemy, run `alembic upgrade head` against the temporary database
  before exercising repositories or HTTP routes when such a test is justified.
- Add a migration smoke test that verifies expected tables and
  `alembic_version` exist.
- Add an Alembic drift test with `alembic check` or the equivalent command API.
- Keep delivery integration tests away from SQLAlchemy models and sessions.
- Test exception translation at the adapter boundary when callers depend on it.
- HTTP adapter tests use `httpx2.MockTransport` or a bounded stub server, not
  legacy `httpx` imports. Route helpers use
  `httpx2.ASGITransport(app=manager.app)` inside `LifespanManager`; HTTPX2 does
  not trigger ASGI lifespan itself.
- Use the production database family when dialect behavior, constraints,
  locking, or query semantics matter. A SQLite substitute is not proof of
  PostgreSQL or MySQL behavior.
- Do not add generic CRUD round-trip repository tests, model declaration tests,
  or session factory tests just to prove SQLAlchemy, Redis, HTTP clients, or
  other upstream libraries work.

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
