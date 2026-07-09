---
name: specx-project-structure
description: Create or reshape a Python service repo into the Specx clean core/delivery architecture using packaged scoped foundation bases. Use when starting a backend repo, adding the first src package, or establishing `AGENTS.md`, `core/`, optional local `foundation/`, `delivery/`, infrastructure, `ioc/`, migrations, and tests.
---

# Specx Project Structure

Use this skill to create the repo shell and first runnable vertical slice. For
details, read `references/blueprint.md`.

## Workflow

1. Derive the import package from the project name: lowercase, hyphen to
   underscore, valid Python identifier.
2. Create `src/<package>/` and `tests/` packages with empty `__init__.py` files only.
3. Add `specx` as a runtime dependency and import base classes from
   `specx.core.foundation`, `specx.delivery.foundation`, or
   `specx.infrastructure.foundation`.
4. Use `core/<scope>/` as the main boundary. Put application packages at the
   scope root: `capabilities/`, `dtos/`, `entities/`, `exceptions/`,
   `gateways/`, `repositories/`, `services/`, and `use_cases/`. Put
   scope-owned technical adapters under `infrastructure/` only when real IO
   exists.
5. Add top-level `delivery/` for runnable framework apps, controllers,
   request/response schemas, and delivery-only services.
6. Add top-level `infrastructure/` for shared technical resources such as
   SQLAlchemy session factories, logging, telemetry, and external client
   factories.
7. Add `ioc/` for `diwire.Container` creation and explicit bindings.
8. Add `shared/` only for stable cross-scope application primitives such as
   unit-of-work contracts, clocks, ids, or errors.
9. Add `migrations/` with Alembic when SQLAlchemy models exist.
10. Create a reusable `core/health` operational probe slice plus delivery
   `/healthz` and `/readyz` routes as the first runnable slice when the user
   asks for a new API repo from scratch.
11. Create root `AGENTS.md` for every new repo. Include runnable project
   commands from `$specx-project-tooling` and Specx boundaries from
   `$specx-component-architecture`.
12. Do not create an empty local `foundation/` package. Create
   `src/<package>/foundation/` only for a real project-local base category or a
   stateful framework base that must not be shared globally, such as a
   SQLAlchemy declarative base.
13. Add tests only where there is real code to test. Do not create empty folders
   just to satisfy the diagram.

## Hard Rules

- Keep all source and test `__init__.py` files empty.
- Under `tests/`, only suite folders such as `unit`, `integration`, and
  `guardrails` are public. Put private helper code under `tests/_support`.
- Required generated tests are currently scoped to core services, use cases,
  and capabilities.
- Tests mirror source module paths directly with flat files such as
  `tests/unit/core/tasks/services/test_title_service.py`.
- Unit tests receive a fresh native pytest `container` fixture, register
  overrides before resolution, and resolve project classes with
  `container.resolve(Target)`.
- Keep class-based test doubles in the `test_*.py` module that uses them.
  Inline `MagicMock` or `AsyncMock` in the test function for one-off behavior.
- Do not create target test folders, `harness.py`, target factories, target
  harnesses, `tests/_support/fakes`, `tests/**/_fakes.py`, generic
  `_scenarios.py`, or double classes in `conftest.py`.
- Before adding a test, sanity-check that it would fail for a plausible bug and
  that its assertion protects behavior, a boundary, or a contract.
- Do not add tests only to have mirrored files, and do not prove upstream
  libraries work.
- Integration tests must use the real internal app graph; do not mock internal
  use cases, services, or capabilities.
- Core use-case integration tests live under `tests/integration/core/...`;
  delivery integration tests live under `tests/integration/delivery/...`.
- Business FastAPI routes use full `/api/v1/...` paths. Operational probes are
  the only unversioned exception: `/healthz` and `/readyz`.
- Reusable probe behavior lives under `core/health`: DTOs, liveness/readiness
  services, `CheckLivenessUseCase`, `CheckReadinessUseCase`, and readiness
  gateway ports. Delivery layers call these use cases and map DTOs to the
  framework response shape.
- `/healthz` is a lightweight liveness-style process probe and must not query
  databases, queues, caches, network services, or SDKs.
- `/readyz` reports whether the instance can receive traffic; SQLAlchemy
  services check database readiness with a cheap bounded `SELECT 1` in a
  `core/health/infrastructure/sqlalchemy` readiness gateway adapter.
- Probe responses stay tiny, use `200` for pass, `503` for not ready, include
  `Cache-Control: no-store`, and do not expose secrets, topology, or stack
  traces.
- FastAPI route tests compare response status codes with `fastapi.status`
  constants, not raw integer literals.
- Use native pytest fixtures for test DI. Do not enable
  `diwire.integrations.pytest_plugin`, and do not use `Injected[...]` test
  parameters.
- Every project class must inherit an explicit base class.
- Prefer packaged bases such as `specx.core.foundation.dto.BaseDTO`,
  `specx.core.foundation.command.BaseCommand`,
  `specx.core.foundation.use_case.BaseUseCase`,
  `specx.core.foundation.pure_service.BasePureService`,
  `specx.core.foundation.read_service.BaseReadService`,
  `specx.core.foundation.effect_service.BaseEffectService`,
  `specx.core.foundation.capability.BaseCapability`,
  `specx.core.foundation.gateway.BaseGateway`, and
  `specx.delivery.foundation.fastapi.schema.BaseFastAPISchema`.
- Every major class should have a docstring that explains the class scope and
  includes a concrete `Example:`.
- Use blank lines as logical separators in all code. Keep related statements
  together, but separate independent setup, action, assertion, response, branch,
  and transformation groups so long blocks stay readable.
- Do not create an empty local `foundation/` package. Add a project-local
  foundation base only when a real project-local base category exists or a
  stateful framework base must own project-local state. Do not copy packaged
  stateless bases locally.
- Do not add `base_` prefixes to local foundation module filenames. Class names
  stay prefixed, for example `clock.py` defines `BaseClock`.
- Core application code (`capabilities/`, `dtos/`, `entities`, `exceptions/`,
  `gateways/`, `repositories/`, `services/`, `use_cases/`) must not import
  FastAPI, SQLAlchemy, Redis, HTTP clients, `delivery`, or the DI container.
- Capabilities inherit `BaseCapability`, live under
  `core/<scope>/capabilities/`, do one narrow injectable thing, and do not own
  workflows, open UoW scopes, or act as repositories/gateways/services.
- Gateway ports inherit `BaseGateway`, live under `core/<scope>/gateways/`, use
  business language, declare external effects in docstrings, and do not return
  entities.
- Concrete gateway implementations live under
  `core/<scope>/infrastructure/<technology>/`.
- Do not put a `delivery/` folder under `core/<scope>/`.
- Delivery maps framework input/output and calls use cases, including the
  `core/health` probe use cases for `/healthz` and `/readyz`.
- Every class under a `services/` package must end with `Service`. Core
  services choose `BasePureService`, `BaseReadService`, or `BaseEffectService`;
  do not create a generic `BaseService`.
- Use cases open UoW scopes. Core services may use an active UoW passed by a
  use case, but services must not open UoW scopes or own commit/rollback.
- Use cases do not inject repositories, active UoWs, providers, SQLAlchemy
  sessions/engines/session factories, or concrete infrastructure adapters
  directly.
- Use-case input classes inherit `BaseCommand` or `BaseQuery`, not `BaseDTO`.
  They live beside the use case and are not result DTOs.
- Infrastructure contains technical IO only. No business decisions there.
- SQLAlchemy schema is managed with Alembic migrations, not application
  `metadata.create_all` calls.
- `ioc/` and top-level delivery `__main__.py`/factory modules may import across
  layers to compose the app.
- Prefer one primary public class per file.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
- Use `BaseStrEnum` for limited known application value sets instead of plain
  `str` or `Literal[...]`.
- Prefer `@dataclass(kw_only=True, slots=True)` for services, use cases,
  controllers, factories, adapters, and similar non-Pydantic behavior classes.
- Generated projects must include root `AGENTS.md`. Keep its Commands section
  aligned with the Makefile and include only commands that exist in that
  project.

## References

- `references/blueprint.md` - target tree, starter files, and creation checklist.
