# specx Delivery Controller Reference

Delivery controllers adapt framework requests to core use cases. Keep them under
top-level `delivery/`, not under `core/<scope>/`.

## Contents

- [FastAPI scope controller](#fastapi-scope-controller)
- [Delivery services](#delivery-services)
- [Schemas](#schemas)
- [App factory registration](#app-factory-registration)
- [FastAPI lifecycle](#fastapi-lifecycle)
- [Integration test](#integration-test)
- [Route rules](#route-rules)

## FastAPI Scope Controller

```python
from dataclasses import dataclass
from http import HTTPStatus

from diwire import Injected
from fastapi import APIRouter, HTTPException

from order_service.core.users.exceptions.user_already_exists import (
    UserAlreadyExistsError,
)
from order_service.core.users.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from order_service.delivery.fastapi.schemas.users_schema import (
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
)
from specx.delivery.foundation.controller import BaseController


@dataclass(kw_only=True, slots=True)
class UsersController(BaseController[APIRouter]):
    """FastAPI controller that registers user routes.

    Example:
        UsersController(_register_user_use_case=use_case).register(router)
    """

    _register_user_use_case: Injected[RegisterUserUseCase]

    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            path="/api/v1/users",
            endpoint=self.register_user,
            methods=["POST"],
            response_model=RegisterUserResponseSchema,
            status_code=HTTPStatus.CREATED,
        )

    async def register_user(
        self,
        request: RegisterUserRequestSchema,
    ) -> RegisterUserResponseSchema:
        try:
            result = await self._register_user_use_case.execute(
                command=RegisterUserCommand(
                    email=str(request.email),
                    password=request.password.get_secret_value(),
                ),
            )
        except UserAlreadyExistsError as exception:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="A user with that email already exists.",
            ) from exception

        return RegisterUserResponseSchema(user_id=result.user_id)
```

Add related routes for the same scope to the same controller. Split only when
the delivery surface has a real boundary difference, such as a different
transport, lifecycle, authentication model, or route group ownership.

## Delivery Services

Controller-only logic lives in `delivery/<framework>/services/`:

```python
from dataclasses import dataclass
from uuid import UUID

from fastapi import Request

from specx.delivery.foundation.service import BaseDeliveryService


@dataclass(kw_only=True, slots=True)
class RequestIdReadingService(BaseDeliveryService):
    """Delivery service that reads a validated request correlation ID.

    Example:
        request_id = service.read(request=request)
    """

    def read(self, *, request: Request) -> UUID | None:
        value = request.headers.get("x-request-id")
        if value is None:
            return None

        try:
            return UUID(value)
        except ValueError:
            return None
```

Use delivery services for auth dependencies, rate limiting, request context,
framework-specific validation, or response metadata. Do not move those helpers
into core unless they become framework-independent application behavior.
Delivery service class names must end with `Service`.

Never treat a client-supplied identity header as an authenticated principal.
Authentication delivery services must verify credentials through the selected
security mechanism and pass only the resulting identity into the command or
query.

A simple process-only `/healthz` response can stay in delivery without a core
workflow. Put operational behavior under `core/health` when readiness checks
any required external dependency or probe policy is reused by multiple
deliveries. In that case, FastAPI probe controllers call the relevant use
cases and map their DTOs to delivery schemas and HTTP status codes.

## Schemas

```python
from pydantic import EmailStr, SecretStr

from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema


class RegisterUserRequestSchema(BaseFastAPISchema):
    """FastAPI request schema for user registration.

    Example:
        RegisterUserRequestSchema(email="ada@example.com", password="secret")
    """

    email: EmailStr
    password: SecretStr


class RegisterUserResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for user registration.

    Example:
        RegisterUserResponseSchema(user_id=1)
    """

    user_id: int
```

Schemas live in delivery. Result DTOs live in the core `dtos/` package.
Commands and queries live in the same file as their use case.

`EmailStr` requires the optional `email-validator` runtime dependency. Add it
only when a schema actually uses email validation. Use secret-aware Pydantic
types for incoming credentials so schema representations do not expose them;
unwrap a secret only when mapping it to the core input that needs the value.

## App Factory Registration

```python
from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, FastAPI

from order_service.delivery.fastapi.controllers.users import UsersController
from order_service.delivery.fastapi.lifecycle import FastAPILifecycle
from specx.core.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class FastAPIFactory(BaseFactory):
    """Factory that composes the FastAPI app and route controllers.

    Example:
        app = FastAPIFactory(
            _lifecycle=lifecycle,
            _users_controller=controller,
        )()
    """

    _lifecycle: Injected[FastAPILifecycle]
    _users_controller: Injected[UsersController]

    def __call__(self) -> FastAPI:
        app = FastAPI(
            title="Order Service",
            redoc_url=None,
            lifespan=self._lifecycle,
        )
        users_router = APIRouter(tags=["users"])
        self._users_controller.register(users_router)
        app.include_router(users_router)
        return app
```

## FastAPI Lifecycle

Put FastAPI lifespan ownership in `delivery/fastapi/lifecycle.py`:

```python
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from diwire import Container, Injected
from fastapi import FastAPI

from order_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from specx.delivery.foundation.lifecycle import BaseLifecycle


@dataclass(kw_only=True, slots=True)
class FastAPILifecycle(BaseLifecycle[FastAPI]):
    """FastAPI lifespan manager for application-owned resources.

    Example:
        lifecycle = FastAPILifecycle(
            _container=container,
            _session_factory=session_factory,
        )
    """

    _container: Injected[Container]
    _session_factory: Injected[SQLAlchemySessionFactory]

    def __call__(self, app: FastAPI) -> AbstractAsyncContextManager[None]:
        return self._lifespan(app=app)

    @asynccontextmanager
    async def _lifespan(self, *, app: FastAPI) -> AsyncIterator[None]:
        del app

        try:
            yield
        finally:
            try:
                await self._session_factory.close()
            finally:
                await self._container.aclose()
```

The lifecycle is the only generated class allowed to inject
`diwire.Container`, and only so it can close the container on shutdown. Do not
run migrations, schema creation, business workflows, or request handling in
lifespan. Keep the nested `finally` blocks: closing one resource must not prevent
later cleanup, and the container must close last.

## Integration Test

```python
import pytest
from diwire import Container
from fastapi import status

from tests._support.clients.fastapi import open_test_async_client


@pytest.mark.anyio
async def test_register_user_returns_created_user(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        response = await client.post(
            "/api/v1/users",
            json={"email": "ada@example.com", "password": "secret"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"user_id": 123}
```

FastAPI integration tests use the real internal app graph and transactional
database. Do not mock use cases or services here; keep those checks in unit
tests.

The generic FastAPI test client helper must run ASGI lifespan explicitly before
opening `AsyncClient`; HTTPX2 transports do not trigger lifespan by themselves.
Inside `LifespanManager`, pass `manager.app` rather than the original app to
`ASGITransport` so request handlers receive any lifespan state.

Use `fastapi.status` constants for response status assertions instead of raw
integer literals.

## Route Rules

- Use full public business paths beginning with `/api/v1/`.
- Use unversioned `/healthz` and `/readyz` only for operational probes.
- Keep probe routes tiny, app-layer unauthenticated, excluded from OpenAPI with
  `include_in_schema=False`, and protected from caching with
  `Cache-Control: no-store`.
- `/healthz` must not query databases, queues, caches, network services, or
  external SDKs.
- `/readyz` checks required infrastructure and returns `503` when the instance
  should not receive traffic.
- Implement any required-dependency readiness or cross-delivery probe policy
  under `core/health`; keep a simple process liveness response and all framework
  headers, status codes, and OpenAPI exclusion in delivery.
- Do not set `APIRouter(prefix="/api/v1")`.
- Do not split path fragments between router and endpoint.
- Keep controller methods thin.
- Do not import infrastructure in controllers.
- Map known application failures to stable delivery messages; never return raw
  exception text, credentials, or infrastructure details.
- Do not use bare controllers, schemas, factories, or delivery services.
