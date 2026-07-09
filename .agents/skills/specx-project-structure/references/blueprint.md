# Specx Project Blueprint

Use this reference to create a new Python backend repo from scratch.

## Target Package Shape

For project `order-service`, use package `order_service`:

```text
AGENTS.md
src/order_service/
  __init__.py
  foundation/
    __init__.py
    sqlalchemy_model.py  # only when SQLAlchemy models exist
  core/
    __init__.py
    health/
      dtos/health_probe_dto.py
      gateways/readiness_check_gateway.py
      infrastructure/sqlalchemy/readiness_check_gateway.py
      services/liveness_probe_service.py
      services/readiness_probe_service.py
      use_cases/check_liveness.py
      use_cases/check_readiness.py
  delivery/
    fastapi/
      __main__.py
      factory.py
      controllers/probes.py
      schemas/probe_schema.py
  infrastructure/
    settings.py
  ioc/
    container.py
tests/
  __init__.py
  _support/
    clients/
    db/
    integration.py
  unit/
    __init__.py
    conftest.py
    core/
      health/
        services/test_liveness_probe_service.py
        services/test_readiness_probe_service.py
        use_cases/test_check_liveness.py
        use_cases/test_check_readiness.py
  integration/
    __init__.py
    conftest.py
    core/
      health/use_cases/test_check_readiness.py
    delivery/fastapi/controllers/test_probes.py
  guardrails/
    architecture/test_boundaries.py
```

Create only directories that contain real files. Import default bases from the
matching scoped Specx foundation package; do not create an empty local
`foundation/` package. Create `src/<package>/foundation/` only when current code
needs a real project-local base category or a stateful framework base that must
not be shared globally, such as a SQLAlchemy declarative base.

Add `tests/_support/` only when tests need generic clients, DB helpers, or
shared integration resources. One-off project-specific test doubles stay in the
`test_*.py` file that uses them. Reused unit-test doubles live in mirrored
`tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
modules. Add `tests/integration/core/...` for use cases that inject a UoW
manager so persistence-facing behavior is proven against the real
transactional database.

Every created test directory gets an empty `__init__.py`; do not add test
package re-exports or setup behavior there.

When stable cross-scope application primitives exist, add `shared/`. When
SQLAlchemy exists, add `foundation/sqlalchemy_model.py`, top-level
`infrastructure/sqlalchemy/`, `alembic.ini`, and `migrations/` with
`$specx-sqlalchemy-migrations`.

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
- Foundation bases come from `specx.core.foundation`,
  `specx.delivery.foundation`, or `specx.infrastructure.foundation`.
- Add `src/order_service/foundation/` only for project-local base categories or
  stateful framework bases that must not be shared globally, such as the
  project SQLAlchemy declarative base. Do not create an empty local
  `foundation/` package.

## Commands

- Install: `uv sync --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Lint/type/format check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run pytest tests/unit`
- Targeted integration tests: `uv run pytest tests/integration`
- Targeted guardrail tests: `uv run pytest tests/guardrails`

## Architecture Rules

- Controllers call injected use cases and never import infrastructure.
- Project classes inherit explicit bases from the matching scoped Specx
  foundation package.
- Public business FastAPI routes use full `/api/v1/...` paths in controllers.
- Operational probes are the only unversioned route exception: `/healthz` for
  lightweight process liveness and `/readyz` for traffic readiness.
- Reusable probe behavior lives under `core/health`; delivery controllers call
  `CheckLivenessUseCase` and `CheckReadinessUseCase` and map the returned DTOs
  to framework responses.
- `/healthz` must not query databases, queues, caches, network services, or
  external SDKs.
- `/readyz` checks required infrastructure; SQLAlchemy services use a cheap
  bounded `SELECT 1` through a health readiness gateway adapter and return
  `503` when persistence is unavailable.
- Probe responses must be small, unauthenticated at the app layer, omit
  secrets/topology/stack traces, and send `Cache-Control: no-store`.
- Use cases expose exactly one `execute(*, command=...)` or
  `execute(*, query=...)`.
- Command/query classes live in the same use-case module and inherit
  `BaseCommand` or `BaseQuery`, not `BaseDTO`.
- Use cases return DTOs, not entities or raw repository results.
- DTOs live in `core/<scope>/dtos`.
- Capabilities live in `core/<scope>/capabilities`, subclass `BaseCapability`,
  do one narrow injectable thing, and do not act as services, repositories, or
  gateways.
- Gateway ports live in `core/<scope>/gateways`, subclass `BaseGateway`, use
  business language, declare external effects, and do not return entities.
- Concrete gateway implementations live under
  `core/<scope>/infrastructure/<tech>`.
- Core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`, end with `Service`, and do not open UoW scopes.
- Query use cases must not call repository mutators.
- Persistence use cases inject `UnitOfWorkManager`, not repositories, active
  UoWs, providers, SQLAlchemy sessions/engines/session factories, or concrete
  infrastructure adapters directly.
- Only `ioc`, top-level delivery `__main__.py`/factory code, and tests may use
  `diwire.Container`.
- Non-foundation source classes need explicit packaged or local bases,
  matching suffixes, and scoped docstrings with concrete `Example:` blocks.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
- Use `BaseStrEnum` for limited known application value sets instead of plain
  `str` or `Literal[...]`.
- Keep all `__init__.py` files empty.

## Tests

- Tests mirror source module paths under `tests/unit` or `tests/integration`
  with flat `test_<module>.py` files.
- `tests/unit/conftest.py` owns the fresh bare unit `container` fixture.
- `tests/integration/conftest.py` owns the transactional DB-backed
  integration `container` fixture.
- Private test helpers live under `tests/_support`; this is not a test suite.
- Architecture policy wrappers live under `tests/guardrails`.
- Every test directory has an empty `__init__.py`.
- Required generated tests are currently scoped to core services, use cases,
  and capabilities.
- Unit tests register local test doubles or inline mocks before resolving the
  target with `container.resolve(Target)`.
- One-off class-based doubles live in the `test_*.py` module that uses them.
- Reused unit-test doubles live in mirrored
  `tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
  modules.
- Integration tests use the real internal app graph and override only external
  systems or the transactional test session factory.
- Core use-case integration tests live under `tests/integration/core/...` and
  call resolved use cases directly against the transactional DB.
- Delivery integration tests live under `tests/integration/delivery/...` and
  own HTTP route/status/schema/error mapping.
- Core health tests cover liveness/readiness services and use cases. When a
  real readiness adapter exists, add a core integration test proving
  `CheckReadinessUseCase` reports the transactional database as ready.
- Delivery probe tests cover `/healthz`, `/readyz`, readiness failure, and the
  absence of legacy `/api/v1/health`. They assert `Cache-Control: no-store`,
  `503` on readiness failure, and that probe routes stay out of OpenAPI.
- Do not create per-target test folders, `harness.py`, target factories,
  target harnesses, `tests/_support/fakes`, `tests/**/_fakes.py`, fake modules
  outside those mirrored unit port/capability packages, generic
  `_scenarios.py`, or double classes in `conftest.py`.
- Do not hand-build application graphs in tests.
- Before adding a test, sanity-check that it would fail for a plausible bug and
  that its assertion protects behavior, a boundary, or a contract.
- Do not add tests just to have mirrored files. Cover real project behavior,
  not upstream library behavior.
- Do not mock internal use cases, services, or capabilities in integration
  tests.
- Do not add tests that only assert `container.resolve(...)` returns an
  instance.
- FastAPI route tests compare response status codes with `fastapi.status`
  constants, not raw integer literals.
- Do not enable `diwire.integrations.pytest_plugin` or use `Injected[...]`
  parameters in tests; keep test injection explicit with native pytest
  fixtures.
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

For a new API repo, create reusable `core/health` operational probe behavior so
multiple delivery layers can expose the same liveness/readiness contract.
Delivery still owns framework details such as route paths, status codes,
headers, schemas, and OpenAPI exclusion.

Use `$specx-add-core-use-case`, `$specx-add-core-service`,
`$specx-add-delivery-controller`, `$specx-diwire-composition`, and
`$specx-tests` for the concrete implementation details.
