# Specx Scope Boundary Reference

Specx uses scoped core packages, a top-level delivery layer, and a foundation
base-class layer.

## Component Layout

```text
foundation/
  command.py
  dto.py
  entity.py
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
    controller.py
    service.py
    fastapi/
      schema.py
core/<scope>/
  dtos/
  entities/
  exceptions/
  repositories/
  services/
  use_cases/
  infrastructure/
    sqlalchemy/
    redis/
    http/
delivery/
  fastapi/
    app.py
    factory.py
    controllers/
    schemas/
    services/
ioc/
infrastructure/
  sqlalchemy/
  logging/
  telemetry/
shared/
```

Use only the folders needed by real code. Add foundation bases only for class
categories that exist now. Add `delivery/<framework>/services/` only for
delivery-only helpers such as auth, rate limiting, request context, or
controller-specific policies.

## Import Direction

- Foundation may import standard library, pure base dependencies such as
  Pydantic, pydantic-settings, SQLAlchemy declarative base, and framework base
  types when defining explicit project bases. It must not import `core`,
  `delivery`, `ioc`, or scope infrastructure.
- Core inner packages may import only same-scope inner packages, `shared`,
  `foundation`, standard library, and pure domain libraries.
- Scope infrastructure may import same-scope inner packages and technical
  libraries. It must not import delivery.
- Top-level infrastructure contains app-wide technical resources such as
  SQLAlchemy session factories, runtime instrumentation, logging, and telemetry.
- Delivery controllers, schemas, and delivery services may import core use
  cases, DTOs, and application exceptions plus framework APIs.
- Delivery controllers should not import infrastructure directly.
- Delivery app/factory modules may import delivery controllers, top-level
  infrastructure, `ioc`, and factories to compose the runtime. They must not
  import scope infrastructure, ORM models, repositories, or schema DDL helpers.
- `ioc` may import any concrete class needed for composition.
- `core/<scope>/delivery/` is not allowed.

## Foundation Bases

Every project class should inherit an explicit base class. Prefer foundation
bases:

- `BaseDTO`
- `BaseCommand`
- `BaseQuery`
- `BaseEntity`
- `BaseService`
- `BaseUseCase`
- `BaseRepository`
- `BaseUnitOfWork`
- `BaseUnitOfWorkManager`
- `BaseFactory`
- `BaseConfigurator`
- `BaseController`
- `BaseDeliveryService`
- `BaseFastAPISchema`
- `BaseRuntimeSettings`
- `BaseStrEnum`
- `BaseApplicationError`
- `BaseApplicationValueError`
- `BaseSQLAlchemyModel`

It is fine to extend foundation with a new base class when a real class category
appears and no existing base fits. Do not add speculative bases.

## Use Cases vs Services

Use a use case for externally meaningful actions:

- `CreateOrderUseCase`
- `IssueTokenUseCase`
- `ImportCustomersUseCase`

Use a core service for focused reusable application behavior:

- `PasswordHashingService`
- `OrderPricingService`
- `AccessPolicyService`
- `TokenIssuingService`

Use a delivery service only for framework-facing behavior:

- `FastAPIRateLimitingService`
- `BearerTokenReadingService`
- `RequestPrincipalResolvingService`

Do not split classes because there are many nouns. Split only when behavior or
boundary pressure differs.

Every service class under a `services/` package must end with `Service`.

Every major concrete class should include a docstring that states the class
scope and includes a concrete `Example:` block. This applies to use cases,
services, ports, adapters, controllers, factories, settings, DTOs, entities,
schemas, unit-of-work classes, and unit-of-work managers.

## Commands, Queries, DTOs, Schemas, Entities

- Use-case inputs are same-file `Command` or `Query` classes beside the use
  case. Do not put them under `dtos/`.
- Commands inherit `BaseCommand`, use the `Command` suffix, and represent
  state-changing actions.
- Queries inherit `BaseQuery`, use the `Query` suffix, and represent read-only
  operations. Empty queries are still explicit, for example `ListTasksQuery()`.
- Every `execute(...)` method accepts exactly one keyword-only `command` or
  `query` argument.
- Result DTOs under `core/<scope>/dtos/` cross use-case output boundaries and
  inherit `BaseDTO`.
- Use cases return DTOs, not entities. Repositories and domain services may work
  with entities internally, but `execute(...)` maps outward results to DTOs.
- Delivery schemas under top-level `delivery/` model HTTP or framework payloads
  and inherit framework-specific schema bases such as `BaseFastAPISchema`.
- Entities represent application/domain state independent from frameworks.
- Do not pass delivery schemas into core.
- Do not return ORM models from infrastructure into core.

## Ports and Adapters

Use a repository or port ABC under `core/<scope>/repositories/` when:

- the implementation performs external IO;
- a framework object must be hidden from core;
- multiple implementations are selected by configuration;
- tests need to replace a slow or non-deterministic dependency.

Put concrete adapters under `core/<scope>/infrastructure/<technology>/`.

Do not create an ABC only because dependency injection is present.

## Unit Of Work Lifecycle

Use cases that need transactional persistence inject a scope-specific
`UnitOfWorkManager`, not `Provider[UnitOfWork]` and not an active UoW instance.
The use case opens the manager inside `execute(...)`:

```python
async with self._unit_of_work_manager as unit_of_work:
    task = await unit_of_work.tasks.get(task_id=task_id)
```

The active `UnitOfWork` exposes repositories. The manager owns opening
sessions, beginning transactions, committing or rolling back, and closing
resources. Deterministic use cases with no external IO do not need a UoW.
Services may receive the active UoW as a method argument, but services do not
open UoW scopes or call lifecycle methods directly.

## Shared Code

Use top-level `infrastructure/` for app-wide technical resources:

- SQLAlchemy engine/session factories;
- logging and telemetry configurators;
- external SDK/client factories shared across scopes.

Use `shared/` for stable cross-scope application primitives:

- clocks and id generators;
- unit-of-work contracts;
- unit-of-work manager contracts;
- small typed values.

Do not put scope-specific decisions in `shared/` or app-wide technical
resources inside one core scope.

## Architecture Tests Worth Adding

- Core inner packages do not import delivery, infrastructure, or ioc.
- Foundation does not import core, delivery, ioc, or scope infrastructure.
- All source classes have explicit base classes.
- Major source classes have scoped docstrings with concrete examples.
- Non-foundation classes do not directly inherit raw common bases such as
  `BaseModel`, `BaseSettings`, `ABC`, `Exception`, `ValueError`,
  `DeclarativeBase`, `StrEnum`, or `object`.
- `core/<scope>/delivery/` does not exist.
- Delivery controllers do not import infrastructure.
- Infrastructure does not import delivery.
- App code does not call `metadata.create_all` or `drop_all`.
- Core inner packages do not import FastAPI, SQLAlchemy, Redis, or HTTP
  clients.
- Only `ioc`, top-level delivery app/factory modules, and tests access
  `diwire.Container`.
- Public HTTP routes use full `/api/v1/...` paths.
