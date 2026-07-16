---
name: specx-component-architecture
description: Design or review Specx core scope boundaries in Python services. Use when deciding where code belongs across packaged scoped foundation bases, optional local foundation extensions, `core/`, capabilities, delivery, infrastructure, `shared/`, and `ioc`; when adding guardrails or splitting use cases, services, DTOs, schemas, ports, and adapters.
---

# Specx Scope Architecture

Use this skill before broad structural changes or when a feature crosses more
than one layer. Read `references/boundaries.md` for the full rules.

## Boundary Model

- `core/<scope>/`: application behavior and contracts. Inner packages are
  `capabilities/`, `dtos/`, `entities`, `exceptions/`, `gateways/`,
  `repositories/`, `services/`, and `use_cases/`.
- `core/<scope>/infrastructure/`: scope-owned external IO adapters such as
  SQLAlchemy repositories, Redis stores, HTTP clients, file storage, and queues.
  Inner core packages must not import it.
- Scoped Specx foundation packages: packaged base classes under
  `specx.core.foundation`, `specx.delivery.foundation`, and
  `specx.infrastructure.foundation`. Every non-foundation source class must
  inherit an explicit packaged base directly or through a project-local base;
  local bases explicitly inherit the packaged or framework base they extend.
- `foundation/`: optional project-local extension point for base definitions
  only: real project-local base categories or stateful framework bases that
  must not be shared globally, such as a SQLAlchemy declarative base.
- `delivery/`: runnable framework apps, controllers, schemas, auth
  dependencies, request parsing, response serialization, HTTP error translation,
  app lifecycle managers, and delivery-only services.
- `infrastructure/`: app-wide technical resources such as SQLAlchemy session
  factories, logging, telemetry, and external client factories.
- Runtime logging lives in top-level `infrastructure/logging`. Configure it
  once with a `BaseConfigurator`; do not inject `logging.Logger`.
- `shared/`: tiny stable cross-scope primitives. It is not a dumping ground.
- `ioc/`: `diwire` container creation and explicit bindings.

## Decision Rules

- Use a use case for an externally meaningful action.
- Use a service for focused reusable business/application behavior.
- Use a capability for one small replaceable injectable ability that is
  narrower than a service.
- Name every service class with a `Service` suffix.
- Name direct concrete `BaseCapability` subclasses with a `Capability` suffix.
- Do not call small collaborators services by default.
- Core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`; do not add or use a generic `BaseService`.
- Do not add `base_` prefixes to project-local foundation module filenames.
  Class names stay prefixed, for example `clock.py` defines `BaseClock`.
- Use gateway ports under `core/<scope>/gateways/` for outbound business
  capabilities such as OpenAI summaries, payments, email, queues, and external
  APIs. Gateway ports inherit `BaseGateway`, declare external effects, and do
  not return entities.
- Put concrete gateway implementations under
  `core/<scope>/infrastructure/<technology>/`.
- Use packaged scoped Specx foundation bases before adding project-local bases.
- Do not create an empty local `foundation/` package.
- Add a project-local foundation base only when a real project-local base
  category exists or a stateful framework base must own project-local state,
  such as SQLAlchemy `MetaData`.
- Use a port or ABC only for a real external boundary or multiple
  implementations.
- Use one delivery controller per scoped set of use cases.
- Use `core/health` when readiness checks any required external dependency or
  probe policy is reusable across delivery layers. Keep a simple
  framework-specific liveness probe in delivery, and do not invent core probe
  services and use cases solely to satisfy the layer diagram.
- When `core/health` is justified, keep framework route/status/header mapping
  in delivery and technical checks behind gateway adapters.
- Keep request/response schemas in top-level `delivery/`. Keep use-case DTOs in
  `core/<scope>/dtos/`.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type. Keep Pydantic at delivery schemas and settings edges.
- Use `BaseStrEnum` for limited known application value sets instead of plain
  `str` or `Literal[...]`.
- When creating or reshaping a repo, keep root `AGENTS.md` architecture
  guidance aligned with these boundaries.
- Define each use-case input as a same-file `Command` or `Query`: commands are
  state-changing, queries are read-only, and even empty inputs are explicit.
- Keep commands and queries independent from DTOs. They inherit `BaseCommand`
  or `BaseQuery`, not `BaseDTO`, and live beside the use case that consumes
  them.
- Use cases return DTOs, not entities.
- Persistence use cases inject `UnitOfWorkManager` for transactional work and
  open the active UoW inside `execute(...)`. They do not inject repositories,
  SQLAlchemy sessions/engines/session factories, or concrete infrastructure
  adapters directly.
- Services may receive an active UoW from a use case, but services must not
  open UoW scopes or own commit/rollback.
- Give every project source class a docstring that explains scope and includes
  a concrete `Example:`; the packaged rule checks abstract ports, local bases,
  enums, and errors as well as concrete behavior classes.
- Keep controller-only helpers such as auth and rate limiting in `delivery/`.
- Keep FastAPI lifespan ownership in `delivery/fastapi/lifecycle.py`. The
  lifecycle releases app-owned resources and closes the DI container on
  shutdown.
- Keep SQL and external API calls in scope infrastructure adapters.
- Classes that actually emit logs create a private stdlib logger in
  `__post_init__` using the full module plus class name. Do not add logger
  fields to DTOs, entities, commands, queries, or classes with no log records.
- Logs should describe important application events and failures without
  secrets, credentials, request bodies, full external URLs, or infrastructure
  topology.
- Do not create bare classes without explicit bases.
- Packaged framework-neutral guardrails run by default when `select` is
  omitted. New generated projects use `select = ["ALL"]`, which enables every
  rule whose required project surface exists. Projects with a narrower base
  selection enable technology families explicitly, for example
  `extend-select = ["fastapi"]`. Do not copy FastAPI paths or guidance into a
  project that uses another delivery technology.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/boundaries.md` - layout, import rules, naming, and architecture
  test targets.
