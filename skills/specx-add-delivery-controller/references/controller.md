# Specx Delivery Controller Reference

Delivery controllers adapt framework requests to core use cases. Keep them under
top-level `delivery/`, not under `core/<scope>/`.

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
from order_service.foundation.delivery.controller import BaseController


@dataclass(kw_only=True, slots=True)
class UsersController(BaseController):
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
        )

    async def register_user(
        self,
        request: RegisterUserRequestSchema,
    ) -> RegisterUserResponseSchema:
        try:
            result = await self._register_user_use_case.execute(
                command=RegisterUserCommand(
                    email=request.email,
                    password=request.password,
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

from fastapi import Request

from order_service.foundation.delivery.service import BaseDeliveryService


@dataclass(kw_only=True, slots=True)
class RequestPrincipalResolvingService(BaseDeliveryService):
    """Delivery service that reads the current principal from a request.

    Example:
        user_id = service.resolve_user_id(request=request)
    """

    def resolve_user_id(self, *, request: Request) -> str:
        return str(request.headers["x-user-id"])
```

Use delivery services for auth dependencies, rate limiting, request context,
framework-specific validation, or response metadata. Do not move those helpers
into core unless they become framework-independent application behavior.
Delivery service class names must end with `Service`.

## Schemas

```python
from pydantic import EmailStr

from order_service.foundation.delivery.fastapi.schema import BaseFastAPISchema


class RegisterUserRequestSchema(BaseFastAPISchema):
    """FastAPI request schema for user registration.

    Example:
        RegisterUserRequestSchema(email="ada@example.com", password="secret")
    """

    email: EmailStr
    password: str


class RegisterUserResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for user registration.

    Example:
        RegisterUserResponseSchema(user_id=1)
    """

    user_id: int
```

Schemas live in delivery. Result DTOs live in the core `dtos/` package.
Commands and queries live in the same file as their use case.

## App Factory Registration

```python
from order_service.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class FastAPIFactory(BaseFactory):
    """Factory that composes the FastAPI app and route controllers.

    Example:
        app = FastAPIFactory(_users_controller=controller)()
    """

    _users_controller: Injected[UsersController]

    def __call__(self) -> FastAPI:
        app = FastAPI(title="Order Service", redoc_url=None)
        users_router = APIRouter(tags=["users"])
        self._users_controller.register(users_router)
        app.include_router(users_router)
        return app
```

## Integration Test

```python
from fastapi.testclient import TestClient

from order_service.delivery.fastapi.factory import FastAPIFactory


def test_register_user_returns_created_user(container: Container) -> None:
    container.add_instance(FakeRegisterUserUseCase(user_id=123), provides=RegisterUserUseCase)
    app = container.resolve(FastAPIFactory)()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/users",
            json={"email": "ada@example.com", "password": "secret"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": 123}
```

## Route Rules

- Use full public paths beginning with `/api/v1/`.
- Do not set `APIRouter(prefix="/api/v1")`.
- Do not split path fragments between router and endpoint.
- Keep controller methods thin.
- Do not import infrastructure in controllers.
- Do not use bare controllers, schemas, factories, or delivery services.
