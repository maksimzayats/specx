# Specx Project Blueprint

Use this reference to create a new Python backend repo from scratch.

## Target Package Shape

For project `order-service`, use package `order_service`:

```text
AGENTS.md
src/order_service/
  __init__.py
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
      __main__.py
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

Create only directories that contain real files. Import default bases from
`specx.foundation`; create `src/<package>/foundation/` only when a real class
category is missing from the package and current code needs that local base.
Add `core/<scope>/capabilities/` only when the scope
has small injectable collaborators narrower than services. Add
`core/<scope>/gateways/` only when the scope has real outbound capabilities such
as OpenAI, payments, email, queues, or external HTTP APIs. Add
`core/<scope>/infrastructure/` only when the scope has technical IO adapters.
Add `delivery/<framework>/services/` only when controllers need delivery-only
helpers such as auth or rate limiting. Keep every `__init__.py` empty.

When stable cross-scope application primitives exist, add `shared/`. When
SQLAlchemy exists, add top-level `infrastructure/sqlalchemy/`, `alembic.ini`,
and `migrations/` with `$specx-sqlalchemy-migrations`.

## Root AGENTS.md

Create root `AGENTS.md` for every generated repo. Keep it concise, practical,
and aligned with the actual Makefile targets. Include only commands that exist
for that project.

Recommended content:

```markdown
# Agent Instructions

## Project Shape

- Package lives under `src/order_service`.
- FastAPI entrypoint: `order_service.delivery.fastapi.__main__:app`.
- Core behavior lives in `src/order_service/core/<scope>/`.
- Delivery lives in `src/order_service/delivery`.
- Shared technical infrastructure lives in `src/order_service/infrastructure`.
- Scope-owned adapters live under `core/<scope>/infrastructure`.
- DI composition lives in `src/order_service/ioc/container.py`.
- Foundation bases come from `specx.foundation`; add
  `src/order_service/foundation/` only for project-local bases missing from the
  package.

## Commands

- Install: `uv sync --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Lint/type/format check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run pytest tests/unit`
- Targeted integration tests: `uv run pytest tests/integration`
- Targeted architecture tests: `uv run pytest tests/architecture`

## Architecture Rules

- Controllers call injected use cases and never import infrastructure.
- Project classes inherit explicit bases, usually from `specx.foundation`.
- Public FastAPI routes use full `/api/v1/...` paths in controllers.
- Use cases expose exactly one `execute(*, command=...)` or
  `execute(*, query=...)`.
- Command/query classes live in the same use-case module.
- Use cases return DTOs, not entities or raw repository results.
- DTOs live in `core/<scope>/dtos`.
- Capabilities live in `core/<scope>/capabilities`, subclass `BaseCapability`,
  do one narrow injectable thing, and do not act as services, repositories, or
  gateways.
- Direct concrete `BaseCapability` subclasses end with `Capability`; narrower
  foundation families such as `BaseClock` or `BaseGenerator` use their narrower
  suffix.
- Do not copy packaged foundation bases into the project. If a local foundation
  base is needed, do not use a `base_` module prefix; for example `clock.py`
  defines `BaseClock`.
- Gateway ports live in `core/<scope>/gateways`, subclass `BaseGateway`, use
  business language, declare external effects, and do not return entities.
- Concrete gateway implementations live under
  `core/<scope>/infrastructure/<tech>`.
- Core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`, end with `Service`, and do not open UoW scopes.
- Pure services are deterministic and do not depend on UoWs, repositories,
  gateways, clients, settings, clocks, UUID/random/time, SQLAlchemy, Redis, or
  SDKs.
- Read/effect services may use an active UoW passed by a use case, but they do
  not open UoW scopes or own commit/rollback.
- Read services do not call repository mutators or external write gateways.
- Effect services do not return entities outward or import delivery/framework
  code.
- Query use cases must not call repository mutators.
- Persistence use cases inject `UnitOfWorkManager`, not active UoWs or
  providers.
- Only `ioc`, top-level delivery `__main__.py`/factory code, and tests may use
  `diwire.Container`.
- Non-foundation source classes need explicit packaged or local bases,
  matching suffixes, and scoped docstrings with concrete `Example:` blocks.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
- Prefer `@dataclass(kw_only=True, slots=True)` for services, use cases,
  controllers, factories, adapters, and similar non-Pydantic behavior classes.
- Keep all `__init__.py` files empty.
```

When SQLAlchemy/Alembic exists, also add the migration shape, commands, and
rules:

```markdown
## Project Shape

- Alembic migrations live in `migrations`.

## Commands

- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`

## Migrations

- Do not use `create_all()` or `drop_all()` in source or tests.
- Add new SQLAlchemy model modules to Alembic's model loader.
- Generate revisions with `make makemigrations`, review them, then run
  `make migration-check`.
```

Replace `order_service` with the real package name and entrypoint.

## First Vertical Slice

For a new API repo, create a health slice so the app can run and tests can prove
the boundaries.

Core DTO:

```python
from dataclasses import dataclass

from specx.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
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
from specx.foundation.pure_service import BasePureService


@dataclass(kw_only=True, slots=True)
class HealthReporterService(BasePureService):
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
from specx.foundation.query import BaseQuery
from specx.foundation.use_case import BaseUseCase


@dataclass(frozen=True, kw_only=True, slots=True)
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
from specx.foundation.delivery.fastapi.schema import BaseFastAPISchema


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
from specx.foundation.delivery.controller import BaseController


@dataclass(kw_only=True, slots=True)
class HealthController(BaseController[APIRouter]):
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
from specx.foundation.factory import BaseFactory


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

Delivery entrypoint (`delivery/fastapi/__main__.py`):

```python
"""FastAPI runtime entrypoint.

Example:
    uv run uvicorn order_service.delivery.fastapi.__main__:app
"""

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
- Use packaged `specx.foundation` bases. Use `$specx-foundation` only when a
  real missing class category needs a project-local base.
- Give every major class a scoped docstring with a concrete `Example:`.
- Define every use-case input as a same-file `Command` or `Query`, even when
  it has no fields.
- Add tooling with `$specx-project-tooling`.
- Add DI with `$specx-diwire-composition`.
- Add Alembic with `$specx-sqlalchemy-migrations` when SQLAlchemy models exist.
- Create root `AGENTS.md` with project commands and architecture boundaries.
- Add tests with `$specx-tests`, including the tiny `specx` architecture
  wrapper when architecture guardrails are needed.
- Run `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, and `uv run mypy .` when tooling exists.

## Avoid

- Do not put delivery modules under `core/<scope>/`.
- Do not put SQLAlchemy, Redis, HTTP clients, or FastAPI imports in inner
  core application packages.
- Do not add package re-exports to `__init__.py`.
- Do not create empty scope folders for future features.
- Do not add bare `class Foo:` declarations.
- Do not call small collaborators services by default. Use `Service` for
  reusable business/application behavior and `BaseCapability` for small
  replaceable abilities.
- Do not name capabilities `Helper`, `Utils`, `Manager`, or `Dependency`.
- Do not put gateway ports under `repositories/` or concrete gateway
  implementations outside `core/<scope>/infrastructure/<technology>/`.
- Do not return entities from gateways. Return DTOs, primitives, value objects,
  or explicit result objects instead.
- Do not inherit raw common bases such as `BaseModel`, `BaseSettings`, `ABC`,
  `Exception`, `ValueError`, or `DeclarativeBase` outside `specx.foundation` or
  a justified project-local foundation module.
- Do not add a generic `BaseService`; choose `BasePureService`,
  `BaseReadService`, or `BaseEffectService` for every core service.
- Do not add `base_` prefixes to project-local foundation module filenames.
  Class names stay prefixed, for example `clock.py` defines `BaseClock`.
- Do not open UoW scopes inside services. Use cases own transaction lifecycle
  and pass the active UoW into read/effect services when needed.
- Name classes with the suffix implied by their foundation base ancestry, such
  as `CreateTaskCommand`, `ListTasksQuery`, `TaskDTO`, `TaskEntity`,
  `TaskResponseSchema`, `TaskRepository`, `TaskUnitOfWork`,
  `TaskUnitOfWorkManager`, `CreateTaskUseCase`, and
  `TaskTitleNormalizerService`.
- Do not return entities from use cases. Return DTOs from `execute(...)`.
