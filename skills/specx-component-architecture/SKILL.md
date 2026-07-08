---
name: specx-component-architecture
description: Design or review Specx core scope boundaries in Python services. Use when deciding where code belongs across `foundation/`, `core/`, capabilities, top-level `delivery/`, top-level infrastructure, scope infrastructure adapters, `shared/`, and `ioc`; when adding import guardrails; or when splitting use cases, services, capabilities, DTOs, schemas, ports, adapters, and foundation bases.
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
- `foundation/`: stable base classes and cross-layer primitives. Every project
  class should inherit an explicit foundation base directly or through another
  project base.
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
- Do not add `base_` prefixes to foundation module filenames. Class names stay
  prefixed, for example `capability.py` defines `BaseCapability`.
- Use gateway ports under `core/<scope>/gateways/` for outbound business
  capabilities such as OpenAI summaries, payments, email, queues, and external
  APIs. Gateway ports inherit `BaseGateway`, declare external effects, and do
  not return entities.
- Put concrete gateway implementations under
  `core/<scope>/infrastructure/<technology>/`.
- Use existing foundation bases before adding new ones.
- Add a new foundation base only when a real class category exists and no
  existing base fits.
- Use a port or ABC only for a real external boundary or multiple
  implementations.
- Use one delivery controller per scoped set of use cases.
- Keep request/response schemas in top-level `delivery/`. Keep use-case DTOs in
  `core/<scope>/dtos/`.
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

## References

- `references/boundaries.md` - layout, import rules, naming, and architecture
  test targets.
