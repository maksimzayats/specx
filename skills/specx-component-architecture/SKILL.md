---
name: specx-component-architecture
description: Design or review Specx core scope boundaries in Python services. Use when deciding where code belongs across packaged `specx.foundation` bases, optional local foundation extensions, `core/`, capabilities, delivery, infrastructure, `shared/`, and `ioc`; when adding guardrails or splitting use cases, services, DTOs, schemas, ports, and adapters.
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
- `specx.foundation`: packaged stable base classes. Every project class should
  inherit an explicit packaged base directly or through a project-local base.
- `foundation/`: optional project-local extension point only when a real class
  category is missing from `specx.foundation`.
- `delivery/`: runnable framework apps, controllers, schemas, auth
  dependencies, request parsing, response serialization, HTTP error translation,
  and delivery-only services.
- `infrastructure/`: app-wide technical resources such as SQLAlchemy session
  factories, logging, telemetry, and external client factories.
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
- Use packaged `specx.foundation` bases before adding project-local bases.
- Add a project-local foundation base only when a real class category exists
  and no packaged base fits.
- Use a port or ABC only for a real external boundary or multiple
  implementations.
- Use one delivery controller per scoped set of use cases.
- Keep request/response schemas in top-level `delivery/`. Keep use-case DTOs in
  `core/<scope>/dtos/`.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type. Keep Pydantic at delivery schemas and settings edges.
- When creating or reshaping a repo, keep root `AGENTS.md` architecture
  guidance aligned with these boundaries.
- Define each use-case input as a same-file `Command` or `Query`: commands are
  state-changing, queries are read-only, and even empty inputs are explicit.
- Use cases return DTOs, not entities.
- Persistence use cases inject `UnitOfWorkManager` for transactional work and
  open the active UoW inside `execute(...)`.
- Services may receive an active UoW from a use case, but services must not
  open UoW scopes or own commit/rollback.
- Give major classes a docstring that explains scope and includes a concrete
  `Example:`.
- Keep controller-only helpers such as auth and rate limiting in `delivery/`.
- Keep SQL and external API calls in scope infrastructure adapters.
- Do not create bare classes without explicit bases.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/boundaries.md` - layout, import rules, naming, and architecture
  test targets.
