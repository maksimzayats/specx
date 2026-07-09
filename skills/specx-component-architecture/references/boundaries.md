# Specx Scope Boundary Reference

Specx uses scoped core packages, a top-level delivery layer, and packaged
foundation bases from scoped Specx foundation packages.

## Component Layout

```text
specx.core.foundation             # core base classes
specx.delivery.foundation         # delivery base classes
specx.infrastructure.foundation   # infrastructure base classes
src/<package>/
  foundation/     # optional local/stateful bases, never empty
core/<scope>/
  capabilities/
  dtos/
  entities/
  exceptions/
  gateways/
  repositories/
  services/
  use_cases/
  infrastructure/
    sqlalchemy/
    redis/
    http/
delivery/
  fastapi/
    __main__.py
    factory.py
    lifecycle.py
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

Use only the folders needed by real code. Import bases from the matching scoped
Specx foundation package by default. Do not create an empty local
`foundation/` package. Add `src/<package>/foundation/` only when a real project-local base
category is missing or a stateful framework base must own project-local state,
such as SQLAlchemy `MetaData`. Add
`delivery/<framework>/services/` only for delivery-only helpers such as auth,
rate limiting, request context, or controller-specific policies.

## Import Direction

- Project-local foundation modules, if present, may import the standard
  library, the needed scoped Specx foundation package, and pure base
  dependencies required by the local base. They must not import `core`,
  `delivery`, `ioc`, or scope infrastructure.
- Core inner packages may import only same-scope inner packages, `shared`,
  `specx.core.foundation`, optional project-local foundation modules, standard
  library, and pure domain libraries.
- Scope infrastructure may import same-scope inner packages, top-level
  infrastructure factories/settings required by its adapter, and technical
  libraries. It must not import delivery.
- Top-level infrastructure contains app-wide technical resources such as
  SQLAlchemy session factories, runtime instrumentation, logging, and telemetry.
- Top-level `infrastructure/logging` owns process-wide stdlib logging
  configuration. It may define `LoggingSettings` and `LoggingConfigurator`; it
  does not define business gateways or injected logger ports.
- Delivery controllers, schemas, and delivery services may import core use
  cases, DTOs, and application exceptions plus framework APIs.
- Delivery controllers should not import infrastructure directly.
- Delivery `__main__.py`, factory, and lifecycle modules may import delivery
  controllers, top-level infrastructure, `ioc`, and factories to compose the
  runtime. They must not import scope infrastructure, ORM models,
  repositories, or schema DDL helpers.
- FastAPI lifecycle code lives in `delivery/fastapi/lifecycle.py`, inherits
  `BaseLifecycle[FastAPI]`, and is the only project class allowed to inject
  `diwire.Container`. It releases app-owned resources and calls
  `container.aclose()` on shutdown.
- `ioc` may import any concrete class needed for composition.
- `core/<scope>/delivery/` is not allowed.

## Foundation Bases

Every project class should inherit an explicit base class. Prefer packaged
scoped Specx foundation bases:

- `BaseDTO`
- `BaseCommand`
- `BaseQuery`
- `BaseEntity`
- `BaseCapability`
- `BaseGateway`
- `BasePureService`
- `BaseReadService`
- `BaseEffectService`
- `BaseUseCase`
- `BaseRepository`
- `BaseUnitOfWork`
- `BaseUnitOfWorkManager`
- `BaseFactory`
- `BaseConfigurator`
- `BaseController`
- `BaseLifecycle`
- `BaseDeliveryService`
- `BaseFastAPISchema`
- `BaseRuntimeSettings`
- `BaseStrEnum`
- `BaseApplicationError`
- `BaseApplicationValueError`

It is fine to add a project-local foundation base when a real class category
appears and no packaged stateless base fits, or when a stateful framework base
must not be shared globally. A project SQLAlchemy declarative base belongs
under `src/<package>/foundation/sqlalchemy_model.py` and owns only that
project's metadata. Do not copy packaged stateless bases locally, and do not add
speculative bases.

## Use Cases, Services, And Capabilities

Use a use case for externally meaningful actions:

- `CreateOrderUseCase`
- `IssueTokenUseCase`
- `ImportCustomersUseCase`

Use a core service for focused reusable application behavior:

- `PasswordHashingService`
- `OrderPricingService`
- `AccessPolicyService`
- `TokenIssuingService`
- `LivenessProbeService`
- `ReadinessProbeService`

Use a capability for small replaceable abilities that are narrower than a
service:

- `SlugGeneratingCapability`
- `PasswordPepperCapability`
- `RequestSigningCapability`

A capability:

- does one narrow thing;
- may be injected, faked, or swapped;
- does not own an application workflow;
- does not open unit-of-work scopes;
- does not act as a repository or gateway;
- is not a generic helper, util, manager, or dependency.

Direct concrete subclasses of `BaseCapability` must end with `Capability`.

When a capability family becomes common or needs stronger review rules, add a
project-local narrower foundation base that inherits from `BaseCapability`,
such as `BaseClock` or `BaseGenerator`. Concrete classes should then use the
narrower suffix: `SystemClock`, `UUID7Generator`, and so on.

Do not add `base_` prefixes to project-local foundation module filenames. Class
names stay prefixed: `clock.py` defines `BaseClock` and `generator.py` defines
`BaseGenerator`.

Do not call small collaborators services by default. Use `Service` for reusable
business/application behavior. Use `BaseCapability` for small replaceable
abilities.

Choose the core service base by effect:

- `BasePureService` for deterministic helpers. Allowed: primitives, entities
  passed as arguments, value objects, DTOs if needed, and other pure services.
  Forbidden: `UnitOfWorkManager`, `UnitOfWork`, repositories, gateways,
  clients, settings, clocks, UUID generators, random/time, HTTP, SQLAlchemy,
  Redis, OpenAI SDK, and other external IO.
- `BaseReadService` for read-only orchestration helpers. Allowed: repository
  reads, preferably through an active UoW passed by the caller; read gateways;
  pure services; and DTO mapping. Forbidden: commit/rollback, repository
  mutators, external write gateways, message publishing, sending email, and
  charging money.
- `BaseEffectService` for helpers that perform or coordinate side effects.
  Allowed: effect gateways, repository mutators through an active UoW passed by
  a command use case, and pure services. Forbidden: opening UoW scopes, owning
  transaction lifecycle, returning entities outward, and importing
  delivery/framework code.

Use a delivery service only for framework-facing behavior:

- `FastAPIRateLimitingService`
- `BearerTokenReadingService`
- `RequestPrincipalResolvingService`

Use a delivery lifecycle for framework-owned startup/shutdown behavior:

- `FastAPILifecycle`

A lifecycle receives long-lived app resources, exposes a framework lifespan
context manager, and closes resources during shutdown. It does not contain
business rules, route mapping, schema serialization, migrations, or request
handling.

Reusable operational health/readiness behavior may live under `core/health`
when more than one delivery could use it. Keep the liveness/readiness DTOs,
services, use cases, and gateway ports in core. Put technical dependency checks
such as SQLAlchemy `SELECT 1`, Redis ping, or queue checks under
`core/health/infrastructure/<technology>/`, and let delivery only map those
use cases to framework-specific routes, headers, status codes, and schemas.

Do not split classes because there are many nouns. Split only when behavior or
boundary pressure differs.

Every service class under a `services/` package must end with `Service`.

Every major concrete class should include a docstring that states the class
scope and includes a concrete `Example:` block. This applies to use cases,
services, ports, adapters, controllers, factories, settings, DTOs, entities,
schemas, unit-of-work classes, and unit-of-work managers.

## Gateways

Use a gateway port for outbound business capabilities to external systems:

- `TaskSummaryGateway` for OpenAI or another summarization provider;
- `PaymentGateway` for payment charging/capture/refund capabilities;
- `EmailGateway` for transactional email;
- `ShipmentGateway` for external shipping APIs.

Gateway ports:

- live under `core/<scope>/gateways/`;
- inherit `BaseGateway`;
- use business language, not SDK, HTTP, queue, or provider details;
- declare external effects in the class docstring with an `External effect:`
  or `External effects:` line;
- return DTOs, primitives, value objects, or explicit result objects, not
  entities or SDK responses.

Concrete gateway implementations:

- live under `core/<scope>/infrastructure/<technology>/`, for example
  `core/tasks/infrastructure/openai/openai_task_summary_gateway.py`;
- inherit the scope gateway port, not `BaseGateway` directly;
- translate SDK/HTTP responses into the gateway return type;
- translate low-level exceptions into core exceptions only when callers need to
  handle them.

Example gateway port:

```python
from order_service.core.tasks.dtos.task_summary_dto import TaskSummaryDTO
from specx.core.foundation.gateway import BaseGateway


class TaskSummaryGateway(BaseGateway):
    """Gateway that generates task summaries.

    External effect: calls a configured text-generation provider.

    Example:
        summary = await gateway.generate_summary(description="Ship the skill")
    """

    async def generate_summary(self, *, description: str) -> TaskSummaryDTO:
        raise NotImplementedError
```

Use repositories for owned persistence. Use gateways for external capabilities
that are not owned persistence, even when the technical implementation is HTTP,
OpenAI, Redis, a queue, or another SDK.

## Commands, Queries, DTOs, Schemas, Entities

- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
- Use `BaseStrEnum` for finite application value sets such as statuses, modes,
  categories, environments, and named operational checks. Do not leave those as
  plain `str` fields when the accepted values are known.
- Use-case inputs are same-file `Command` or `Query` classes beside the use
  case. Do not put them under `dtos/`.
- Commands inherit `BaseCommand`, use the `Command` suffix, and represent
  state-changing actions.
- Queries inherit `BaseQuery`, use the `Query` suffix, and represent read-only
  operations. Empty queries are still explicit, for example `ListTasksQuery()`.
- Commands and queries are use-case input contracts, not DTOs. Keep
  `BaseCommand` and `BaseQuery` independent from `BaseDTO`, and do not place
  input classes under `dtos/`.
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

Use a repository under `core/<scope>/repositories/` when modeling owned
persistence. Use a gateway under `core/<scope>/gateways/` when modeling an
outbound capability provided by an external system.

Use a repository or gateway port when:

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

Use cases do not inject repositories, SQLAlchemy sessions, engines, session
factories, or concrete infrastructure adapters directly. Repository access from
a use case must happen through a variable created by the injected manager
context:

```python
async with self._unit_of_work_manager as unit_of_work:
    task = await unit_of_work.tasks.get(task_id=task_id)
```

Avoid extracting repository aliases inside use cases. Keep repository calls
rooted in the active UoW variable or delegate the persistence behavior to a
read/effect service that receives that active UoW.

Good service call from a use case:

```python
async with self._unit_of_work_manager as unit_of_work:
    return await self._task_completion_service.complete(
        unit_of_work=unit_of_work,
        task_id=command.task_id,
    )
```

Bad service implementation:

```python
async with self._unit_of_work_manager as unit_of_work:
    ...
```

## Shared Code

Use top-level `infrastructure/` for app-wide technical resources:

- SQLAlchemy engine/session factories;
- logging and telemetry configurators;
- external SDK/client factories shared across scopes.

Runtime logging should be configured once through a top-level
`LoggingConfigurator` that inherits `BaseConfigurator` and calls
`logging.config.dictConfig`. Use `disable_existing_loggers=False` so server,
SQLAlchemy, Alembic, and library loggers are not accidentally silenced. Do not
inject `logging.Logger` or register loggers in `diwire.Container`.

When a behavior class actually emits log records, add a private logger field
and initialize it in `__post_init__`:

```python
_logger: logging.Logger = field(init=False, repr=False)

def __post_init__(self) -> None:
    self._logger = logging.getLogger(
        f"{self.__class__.__module__}.{self.__class__.__qualname__}",
    )
```

Do not add logger fields to DTOs, entities, commands, queries, or classes with
no log statements. Log important application events and failures, and avoid
secrets, tokens, request bodies, full external URLs, credentials, and detailed
infrastructure topology.

Use `shared/` for stable cross-scope application primitives:

- clocks and id generators;
- unit-of-work contracts;
- unit-of-work manager contracts;
- small typed values.

Do not put scope-specific decisions in `shared/` or app-wide technical
resources inside one core scope.

## Packaged Architecture Guardrails

Use `specx.testing.architecture` as the default guardrail mechanism instead of
hand-writing local architecture tests for Specx boundaries. The packaged rule
set is exposed through stable `SpecxRuleId` values and covers:

- core import direction, including no delivery, ioc, top-level infrastructure,
  FastAPI, SQLAlchemy, Redis, or HTTP clients from core inner packages;
- project-local foundation import direction, when local foundation modules
  exist;
- explicit source-class bases, scoped example docstrings, foundation-category
  suffixes, and avoidance of raw common bases such as `BaseModel`,
  `BaseSettings`, `ABC`, `Exception`, `ValueError`, `DeclarativeBase`,
  `StrEnum`, or `object`;
- capability placement, suffixes, and avoidance of helper/manager/repository/
  gateway/service roles;
- no `core/<scope>/delivery/` packages;
- delivery controllers avoiding infrastructure imports and infrastructure
  avoiding delivery imports;
- no `metadata.create_all` or `drop_all` calls in source or tests;
- `diwire.Container` access limited to `ioc`, top-level delivery app entry
  points/factories/lifecycles, and tests, with `Injected[Container]` allowed
  only in the FastAPI lifecycle;
- no injected `logging.Logger` dependencies or logger registrations in the DI
  container;
- full `/api/v1/...` public business HTTP route paths, with only `/healthz`
  and `/readyz` allowed as unversioned operational probe routes;
- gateway port and implementation placement, external-effect documentation, and
  no entity returns from gateway methods;
- use-case input placement, command/query semantics, DTO returns, and query
  use cases avoiding repository mutators;
- use cases avoiding direct repository/session/engine/infrastructure
  injection, with repository calls rooted in a manager-owned UoW variable;
- core service suffixes and use of `BasePureService`, `BaseReadService`, or
  `BaseEffectService`;
- pure/read/effect service effect boundaries and UoW lifecycle constraints;
- root `AGENTS.md` project-command and Specx-boundary guidance.

Add custom `extra_rules` only for project-specific policies that the packaged
`SpecxRuleId` set does not cover.
