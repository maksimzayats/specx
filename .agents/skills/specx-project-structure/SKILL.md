---
name: specx-project-structure
description: Create or reshape a Python FastAPI service repo into the Specx clean core/delivery architecture using packaged scoped foundation bases. Use when starting an API backend, adding the first src package, or establishing `AGENTS.md`, `core/`, optional local `foundation/`, `delivery/`, infrastructure, `ioc/`, migrations, and tests.
---

# Specx Project Structure

Use this skill to create the repo shell and first runnable vertical slice. For
details, read `references/blueprint.md`.

## Workflow

1. Preserve an existing import package declared by the repo. For a new repo,
   derive a lowercase underscore name, normalize every non-identifier
   character, and verify `name.isidentifier()` and
   `not keyword.iskeyword(name)`; distribution names and import packages need
   not be identical. If normalization still yields a keyword or leading digit,
   choose an explicit valid package name rather than emitting it unchanged.
2. Create `src/<package>/` and `tests/` packages with empty `__init__.py` files only.
3. Add `specx` as a runtime dependency and import base classes from
   `specx.core.foundation`, `specx.delivery.foundation`, or
   `specx.infrastructure.foundation`.
4. Use `core/<scope>/` as the main boundary. Put application packages at the
   scope root: `capabilities/`, `dtos/`, `entities/`, `exceptions/`,
   `gateways/`, `repositories/`, `services/`, and `use_cases/`. Put
   scope-owned technical adapters under `infrastructure/` only when real IO
   exists.
5. Add top-level `delivery/` for runnable framework apps, lifecycles,
   controllers, request/response schemas, and delivery-only services.
6. Add top-level `infrastructure/` for shared technical resources such as
   SQLAlchemy session factories, logging, telemetry, and external client
   factories. App-owned pooled clients live here even when only one scope
   currently consumes them; bounded short-lived clients may stay with the
   scope adapter.
7. Add `infrastructure/logging/` with a stdlib `LoggingConfigurator` and
   `LoggingSettings` for every new API repo.
8. Add `ioc/` for `diwire.Container` creation and explicit bindings.
9. Add `shared/` only for stable cross-scope application primitives such as
   unit-of-work contracts, clocks, ids, or errors.
10. Add `migrations/` with Alembic when SQLAlchemy models exist.
11. Build the first user-requested business vertical slice. If no domain slice
   is specified, add only the smallest runnable delivery liveness endpoint.
   Add `core/health` behavior and `/readyz` when readiness checks any required
   external dependency or probe policy is shared across deliveries.
12. Create root `AGENTS.md` for every new repo. Include runnable project
   commands from `$specx-project-tooling` and Specx boundaries from
   `$specx-component-architecture`.
13. Do not create an empty local `foundation/` package. Create
   `src/<package>/foundation/` only for a real project-local base category or a
   stateful framework base that must not be shared globally, such as a
   SQLAlchemy declarative base.
14. Add tests only where there is real code to test. Do not create empty folders
   just to satisfy the diagram.

## Non-Negotiable Boundaries

- Keep all source and test `__init__.py` files empty. Do not add empty local
  foundation, source, test, or helper packages.
- Every non-foundation source class inherits an explicit packaged or local
  scoped base and uses the suffix implied by that ancestry. Every source class,
  including local bases, has a scoped docstring with a real `Example:`.
- Keep core inner packages free of delivery, IOC, SQLAlchemy, Redis, HTTP
  clients, and framework imports. Put concrete IO adapters under
  `core/<scope>/infrastructure/<technology>/`.
- Capabilities are narrow `BaseCapability` collaborators; gateways are
  business-language `BaseGateway` ports; core services choose
  `BasePureService`, `BaseReadService`, or `BaseEffectService`.
- Same-file `BaseCommand` or `BaseQuery` inputs enter use cases, and result DTOs
  leave them. Persistence use cases inject a `UnitOfWorkManager`; services do
  not open or finish transactions.
- Prefer frozen, keyword-only, slotted dataclasses for core data and
  `BaseStrEnum` for reusable closed value sets. Keep Pydantic at delivery and
  settings edges.
- Keep infrastructure technical and schema evolution in Alembic. Never call
  `metadata.create_all` or `drop_all` in application or test code.
- Configure stdlib logging once before composing the FastAPI app. Use FastAPI
  lifespan for resource cleanup, then close the container; do not run schema
  changes or business workflows in lifespan.
- Business routes use full `/api/v1/...` paths. Keep `/healthz` independent of
  external systems; use `/readyz` and `core/health` for any required external
  dependency, with bounded checks and minimal responses.
- Mirror real source behavior with flat tests. Unit tests resolve targets from
  a native pytest `container` fixture; integration tests use the real internal
  graph and replace only external boundaries. Read the blueprint before adding
  shared doubles or support helpers.
- Keep root `AGENTS.md` commands aligned with the Makefile and include only
  guidance that matches files and features present in the project.
- This skill and the current packaged delivery guardrails target FastAPI. For a
  worker, CLI, or another web framework, use `$specx-component-architecture`
  and explicitly replace the incompatible FastAPI-specific rules.

## References

- `references/blueprint.md` - target tree, starter files, and creation checklist.
