# Agent Instructions

## Project Shape

- Package lives under `src/task_db_service`.
- FastAPI entrypoint: `task_db_service.delivery.fastapi.__main__:app`.
- Core behavior lives in `src/task_db_service/core/<scope>/`.
- Delivery lives in `src/task_db_service/delivery/fastapi`.
- Shared technical infrastructure lives in `src/task_db_service/infrastructure`.
- Scope-owned adapters live under `core/<scope>/infrastructure`.
- DI composition lives in `src/task_db_service/ioc/container.py`.
- Alembic migrations live in `migrations`.
- Foundation bases come from `specx.foundation`; this sample has no local
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
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`

## Architecture Rules

- Controllers call injected use cases and never import infrastructure.
- Project classes inherit explicit bases from `specx.foundation`.
- Public FastAPI routes use full `/api/v1/...` paths in controllers.
- Use cases subclass `BaseUseCase` and expose exactly one
  `execute(*, command=...)` or `execute(*, query=...)`.
- Command/query classes live in the same use-case module and subclass
  `BaseCommand` or `BaseQuery`.
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
- Do not add local foundation modules unless a real class category is missing
  from `specx.foundation`. Do not use `base_` module prefixes for those local
  extensions.
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
  UoW scope, and must not inject active UoWs or providers.
- Only `ioc/container.py`, top-level delivery `__main__.py`/factory code, and
  tests may use `diwire.Container`.
- Use `Injected[...]` for collaborators.
- Source classes need explicit packaged or local bases,
  matching suffixes, and scoped docstrings with concrete `Example:` blocks.
- Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
  queries, DTOs, entities, and other core data classes unless the user asks for
  another model type.
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
- Test bodies receive resolved components, fakes, mocks, or container-backed
  clients from fixtures. Do not hand-build application graphs in tests or
  support factories.
- Before adding a test, sanity-check that it would fail for a plausible bug and
  that its assertion protects behavior, a boundary, or a contract.
- Add tests only when they make sense. Do not add nonsense tests just to have a
  mirrored file, and do not prove upstream libraries such as SQLAlchemy,
  Alembic, HTTPX, or FastAPI work.
- Integration tests must use the real internal app graph; do not mock internal
  use cases or services.
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
- Preserve naming conventions from `BaseSQLAlchemyModel.metadata`.

## Do Not Touch Without Explicit Request

- Do not hand-edit `uv.lock`; use `uv`.
- Do not add local copies of packaged `specx.foundation` bases for feature work.
- Do not move route paths into router prefixes.
- Do not bypass the DI container by constructing production graphs in delivery.
- Do not edit existing migration revisions casually; add a new revision for
  schema changes.
