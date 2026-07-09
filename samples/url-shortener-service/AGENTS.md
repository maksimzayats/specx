# Agent Instructions

## Project Shape

- Package lives under `src/url_shortener_service`.
- FastAPI entrypoint: `url_shortener_service.delivery.fastapi.__main__:app`.
- Core behavior lives in `src/url_shortener_service/core/<scope>/`.
- Delivery lives in `src/url_shortener_service/delivery/fastapi`.
- Shared technical infrastructure lives in `src/url_shortener_service/infrastructure`.
- Runtime logging is configured by
  `src/url_shortener_service/infrastructure/logging/configurator.py`.
- Scope-owned adapters live under `core/<scope>/infrastructure`.
- DI composition lives in `src/url_shortener_service/ioc/container.py`.
- Alembic migrations live in `migrations`.
- Foundation bases come from `specx.core.foundation`,
  `specx.delivery.foundation`, or `specx.infrastructure.foundation`.
- This sample has a local `foundation/sqlalchemy_model.py` only for the
  project SQLAlchemy declarative base and metadata. Do not add empty local
  foundation packages.

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
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`

## Architecture Rules

- Controllers call injected use cases and never import infrastructure.
- Project classes inherit explicit bases from the matching scoped Specx
  foundation package or the project-local SQLAlchemy declarative base.
- Public business FastAPI routes use full `/api/v1/...` paths in controllers.
- Operational probe routes are the only unversioned route exception:
  `/healthz` checks local process liveness and `/readyz` checks whether the
  instance can serve traffic.
- Reusable probe behavior lives under `core/health`; delivery controllers call
  `CheckLivenessUseCase` and `CheckReadinessUseCase` and map the returned DTOs
  to FastAPI responses.
- `/healthz` must not query databases, queues, caches, network services, or
  external SDKs.
- `/readyz` checks required infrastructure; for this DB-backed service it runs
  a cheap bounded database query through the health SQLAlchemy readiness
  gateway adapter and returns `503` when persistence is not available.
- Probe responses must be small, unauthenticated at the app layer, omit
  secrets/topology/stack traces, and send `Cache-Control: no-store`.
- Runtime logging is configured once by `LoggingConfigurator` in top-level
  `infrastructure/logging` using Python stdlib logging.
- The FastAPI runtime entrypoint resolves `LoggingConfigurator` and calls
  `configure()` before resolving `FastAPIFactory`.
- Do not inject loggers, register `logging.Logger` in the DI container, or pass
  loggers through constructors. Classes that actually log create a private
  class logger in `__post_init__` using the full module plus class name.
- Log important application events and failures, but never secrets, tokens,
  full external URLs, credentials, request bodies, or detailed infrastructure
  topology.
- Use cases subclass `BaseUseCase` and expose exactly one
  `execute(*, command=...)` or `execute(*, query=...)`.
- Command/query classes live in the same use-case module and subclass
  `BaseCommand` or `BaseQuery`.
- Command/query classes are input contracts, not DTOs. They must not inherit
  `BaseDTO` or live under `dtos/`.
- Use cases return DTOs, not entities or raw repository results.
- DTOs live in `core/<scope>/dtos` and subclass `BaseDTO`.
- Small injectable collaborators live in `core/<scope>/capabilities`, subclass
  `BaseCapability`, do one narrow thing, and do not open UoW scopes or act as
  repositories, gateways, helpers, managers, or services.
- Direct concrete subclasses of `BaseCapability` end with `Capability`; narrower
  foundation families such as `BaseClock` or `BaseGenerator` use their narrower
  suffix.
- Gateway ports live in `core/<scope>/gateways`, subclass `BaseGateway`,
  declare external effects, use business language, and do not return entities.
- Concrete gateway implementations live under
  `core/<scope>/infrastructure/<tech>`.
- Core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService` and end with `Service`.
- Do not add local foundation modules unless a real project-local base category
  or stateful framework base is needed. This sample's local foundation exists
  only for the SQLAlchemy declarative base. Do not use `base_` module prefixes
  for local foundation modules.
- Pure services are deterministic and do not depend on UoWs, repositories,
  gateways, clients, settings, clocks, UUID/random/time, SQLAlchemy, Redis, or
  SDKs.
- Read/effect services may use an active UoW passed by a use case, but they do
  not open UoW scopes or own commit/rollback.
- Read services do not call repository mutators or external write gateways.
- Effect services do not return entities outward or import delivery/framework
  code.
- Query use cases must not call repository mutators.
- Use cases that touch persistence inject `UnitOfWorkManager`, open at most one
  UoW scope, and must not inject repositories, active UoWs, providers,
  SQLAlchemy sessions/engines/session factories, or concrete infrastructure
  adapters directly.
- Only `ioc/container.py`, top-level delivery `__main__.py`/factory code, and
  tests may use `diwire.Container`.
- Use `Injected[...]` for collaborators.
- Source classes need explicit packaged or local bases,
  matching suffixes, and scoped docstrings with concrete `Example:` blocks.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
- Use `BaseStrEnum` for limited known application value sets instead of plain
  `str` or `Literal[...]`.
- Prefer `@dataclass(kw_only=True, slots=True)` for services, use cases,
  controllers, factories, adapters, and similar non-Pydantic behavior classes.
- Use blank lines as logical separators in all code. Keep related statements
  together, but separate independent setup, action, assertion, response, branch,
  and transformation groups so long blocks stay readable.
- Keep all `__init__.py` files empty.

## Tests

- Tests mirror source module paths under `tests/unit` or `tests/integration`.
- Private test helpers live under `tests/_support`; this is not a test suite.
- Architecture policy wrappers live under `tests/guardrails`.
- Required generated tests are currently scoped to core services, use cases,
  and capabilities.
- Unit tests cover core services/use cases with fresh `diwire` test containers
  and typed fakes for replaced ports; they do not use FastAPI, SQLAlchemy
  sessions, or real IO.
- Integration tests cover core use cases, FastAPI routes, and Alembic
  migrations only when they protect project-owned behavior.
- Core use-case integration tests live under `tests/integration/core/...` and
  call resolved use cases directly against the transactional DB.
- Delivery integration tests live under `tests/integration/delivery/...` and
  own HTTP route/status/schema/error mapping.
- Core health tests cover liveness/readiness services and use cases. The
  readiness integration test proves the real SQLAlchemy readiness adapter
  reports the transactional database as ready.
- Delivery probe tests cover `/healthz`, `/readyz`, readiness failure, and the
  absence of legacy `/api/v1/health`.
- Unit tests cover `LoggingConfigurator` by overriding `LoggingSettings`,
  monkeypatching `logging.config.dictConfig`, and asserting the generated
  readable stdlib config. Use `caplog` only when a log record protects
  meaningful project behavior.
- Core service/use-case/capability tests mirror source module paths with flat
  `test_<module>.py` files.
- Unit tests receive the native pytest `container` fixture, register local
  doubles or inline mocks before resolution, and resolve project classes with
  `container.resolve(Target)`.
- Delivery tests use generic container-backed helpers such as
  `open_test_async_client(container)` so overrides happen before app creation.
- One-off class-based test doubles live in the `test_*.py` module that uses
  them. Reused unit-test doubles live in mirrored
  `tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
  modules.
- Inline `MagicMock` or `AsyncMock` in the test function for one-off behavior.
- Do not create per-target test folders, `harness.py`, target factories,
  target harnesses, `tests/_support/fakes`, `tests/**/_fakes.py`, fake modules
  outside those mirrored unit port/capability packages, generic
  `_scenarios.py`, or double classes in `conftest.py`.
- Before adding a test, sanity-check that it would fail for a plausible bug and
  that its assertion protects behavior, a boundary, or a contract.
- Add tests only when they make sense. Do not add nonsense tests just to have a
  mirrored file, and do not prove upstream libraries such as SQLAlchemy,
  Alembic, HTTPX, or FastAPI work.
- Integration tests must use the real internal app graph; do not mock internal
  use cases, services, or capabilities.
- FastAPI route tests should compare response status codes with
  `fastapi.status` constants, not raw integer literals.
- Mock fixtures should register one external collaborator for the behavior
  under test. Do not bundle unrelated mocks in a dict or class-keyed fixture.
- Do not add tests that only assert `container.resolve(...)` returns an
  instance.
- Do not enable `diwire.integrations.pytest_plugin` or use `Injected[...]`
  parameters in tests; keep test injection explicit with native pytest fixtures.
- Override dependencies before resolving the graph. Resolve factories first,
  then call them.
- Architecture tests are part of the contract; update them only for intentional
  architecture changes.
- DB integration tests use Alembic schema setup and per-test transactional
  rollback unless the migration itself is under test.

## Migrations

- Do not use `create_all()` or `drop_all()` in source or tests.
- Add model modules under the SQLAlchemy model package; Alembic discovers them
  from `core/*/infrastructure/sqlalchemy/models`.
- Generate revisions with `make makemigrations`, review them, then run
  `make migration-check`.
- Preserve naming conventions from the project-local
  `BaseSQLAlchemyModel.metadata`.

## Do Not Touch Without Explicit Request

- Do not hand-edit `uv.lock`; use `uv`.
- Do not add local copies of packaged scoped foundation bases for feature work.
  Local foundation modules are only for real project-local base categories or
  stateful framework bases such as the SQLAlchemy declarative base.
- Do not move route paths into router prefixes.
- Do not bypass the DI container by constructing production graphs in delivery.
- Do not edit existing migration revisions casually; add a new revision for
  schema changes.
