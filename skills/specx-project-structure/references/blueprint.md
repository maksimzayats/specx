# Specx Project Blueprint

Use this reference to create a new Python backend repo from scratch.

## Target Package Shape

For project `order-service`, use package `order_service`:

```text
src/order_service/
  __init__.py
  foundation/
    __init__.py
    command.py
    dto.py
    entity.py
    enums.py
    exceptions.py
    factory.py
    repository.py
    query.py
    service.py
    settings.py
    unit_of_work.py
    unit_of_work_manager.py
    use_case.py
    delivery/
      __init__.py
      controller.py
      service.py
      fastapi/
        __init__.py
        schema.py
    infrastructure/
      __init__.py
      sqlalchemy/
        __init__.py
        model.py
  core/
    __init__.py
    health/
      __init__.py
      dtos/
        __init__.py
        health_status_dto.py
      services/
        __init__.py
        health_reporter_service.py
      use_cases/
        __init__.py
        check_health.py
  delivery/
    __init__.py
    fastapi/
      __init__.py
      app.py
      factory.py
      controllers/
        __init__.py
        health.py
      schemas/
        __init__.py
        health_schema.py
  infrastructure/
    __init__.py
    settings.py
  ioc/
    __init__.py
    container.py
tests/
  unit/
  integration/
  architecture/
```

Create only directories that contain real files. Add only the foundation bases
needed by current classes. Add `core/<scope>/infrastructure/` only when the
scope has technical IO adapters. Add `delivery/<framework>/services/` only when
controllers need delivery-only helpers such as auth or rate limiting. Keep every
`__init__.py` empty.

When stable cross-scope application primitives exist, add `shared/`. When
SQLAlchemy exists, add top-level `infrastructure/sqlalchemy/`, `alembic.ini`,
and `migrations/` with `$specx-sqlalchemy-migrations`.

## First Vertical Slice

For a new API repo, create a health slice so the app can run and tests can prove
the boundaries.

Core DTO:

```python
from order_service.foundation.dto import BaseDTO


class HealthStatusDTO(BaseDTO):
    """DTO returned by health use cases.

    Example:
        HealthStatusDTO(status="ok")
    """

    status: str
```

Core service:

```python
from dataclasses import dataclass

from order_service.core.health.dtos.health_status_dto import HealthStatusDTO
from order_service.foundation.service import BaseService


@dataclass(kw_only=True, slots=True)
class HealthReporterService(BaseService):
    """Service that reports deterministic application health state.

    Example:
        status = HealthReporterService().check()
    """

    def check(self) -> HealthStatusDTO:
        return HealthStatusDTO(status="ok")
```

Core use case:

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.health.dtos.health_status_dto import HealthStatusDTO
from order_service.core.health.services.health_reporter_service import (
    HealthReporterService,
)
from order_service.foundation.query import BaseQuery
from order_service.foundation.use_case import BaseUseCase


class CheckHealthQuery(BaseQuery):
    """Query for reading application health status.

    Example:
        CheckHealthQuery()
    """


@dataclass(kw_only=True, slots=True)
class CheckHealthUseCase(BaseUseCase):
    """Use case that exposes health status to delivery layers.

    Example:
        status = use_case.execute(query=CheckHealthQuery())
    """

    _health_reporter_service: Injected[HealthReporterService]

    def execute(self, *, query: CheckHealthQuery) -> HealthStatusDTO:
        _ = query
        return self._health_reporter_service.check()
```

Delivery schema:

```python
from order_service.foundation.delivery.fastapi.schema import BaseFastAPISchema


class HealthResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for health status.

    Example:
        HealthResponseSchema(status="ok")
    """

    status: str
```

Delivery controller:

```python
from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter

from order_service.core.health.use_cases.check_health import (
    CheckHealthQuery,
    CheckHealthUseCase,
)
from order_service.delivery.fastapi.schemas.health_schema import HealthResponseSchema
from order_service.foundation.delivery.controller import BaseController


@dataclass(kw_only=True, slots=True)
class HealthController(BaseController):
    """FastAPI controller that registers health routes.

    Example:
        HealthController(_check_health_use_case=use_case).register(router)
    """

    _check_health_use_case: Injected[CheckHealthUseCase]

    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            path="/api/v1/health",
            endpoint=self.check_health,
            methods=["GET"],
            response_model=HealthResponseSchema,
        )

    def check_health(self) -> HealthResponseSchema:
        status = self._check_health_use_case.execute(query=CheckHealthQuery())
        return HealthResponseSchema.model_validate(status)
```

FastAPI factory:

```python
from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, FastAPI

from order_service.delivery.fastapi.controllers.health import HealthController
from order_service.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class FastAPIFactory(BaseFactory):
    """Factory that composes the FastAPI app.

    Example:
        app = FastAPIFactory(_health_controller=controller)()
    """

    _health_controller: Injected[HealthController]

    def __call__(self) -> FastAPI:
        app = FastAPI(title="Order Service", redoc_url=None)

        health_router = APIRouter(tags=["health"])
        self._health_controller.register(health_router)
        app.include_router(health_router)

        return app
```

Delivery app:

```python
from order_service.delivery.fastapi.factory import FastAPIFactory
from order_service.ioc.container import get_container

container = get_container()
app = container.resolve(FastAPIFactory)()
```

Container:

```python
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy

def get_container() -> Container:
    return Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
```

## Creation Checklist

- Add package files before tests so imports resolve.
- Add foundation bases with `$specx-foundation`.
- Give every major class a scoped docstring with a concrete `Example:`.
- Define every use-case input as a same-file `Command` or `Query`, even when
  it has no fields.
- Add tooling with `$specx-project-tooling`.
- Add DI with `$specx-diwire-composition`.
- Add Alembic with `$specx-sqlalchemy-migrations` when SQLAlchemy models exist.
- Add tests with `$specx-tests`.
- Run `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, and `uv run mypy .` when tooling exists.

## Avoid

- Do not put delivery modules under `core/<scope>/`.
- Do not put SQLAlchemy, Redis, HTTP clients, or FastAPI imports in inner
  core application packages.
- Do not add package re-exports to `__init__.py`.
- Do not create empty scope folders for future features.
- Do not add bare `class Foo:` declarations.
- Do not inherit raw common bases such as `BaseModel`, `BaseSettings`, `ABC`,
  `Exception`, `ValueError`, or `DeclarativeBase` outside `foundation/` when a
  project foundation base exists.
- Name classes with the suffix implied by their foundation base ancestry, such
  as `CreateTaskCommand`, `ListTasksQuery`, `TaskDTO`, `TaskEntity`,
  `TaskResponseSchema`, `TaskRepository`, `TaskUnitOfWork`,
  `TaskUnitOfWorkManager`, `CreateTaskUseCase`, and
  `TaskTitleNormalizerService`.
- Do not return entities from use cases. Return DTOs from `execute(...)`.
