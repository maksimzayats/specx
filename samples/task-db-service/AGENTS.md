# Agent Instructions

## Project Shape

- Package lives under `src/task_db_service`.
- FastAPI entrypoint: `task_db_service.delivery.fastapi.app:app`.
- Core behavior lives in `src/task_db_service/core/<scope>/`.
- Delivery lives in `src/task_db_service/delivery/fastapi`.
- Shared technical infrastructure lives in `src/task_db_service/infrastructure`.
- Scope-owned adapters live under `core/<scope>/infrastructure`.
- DI composition lives in `src/task_db_service/ioc/container.py`.
- Alembic migrations live in `migrations`.

## Commands

- Install: `uv sync --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Lint/type/format check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run pytest tests/unit`
- Targeted integration tests: `uv run pytest tests/integration`
- Targeted architecture tests: `uv run pytest tests/architecture`
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`

## Architecture Rules

- Controllers call injected use cases and never import infrastructure.
- Public FastAPI routes use full `/api/v1/...` paths in controllers.
- Use cases subclass `BaseUseCase` and expose exactly one
  `execute(*, command=...)` or `execute(*, query=...)`.
- Command/query classes live in the same use-case module and subclass
  `BaseCommand` or `BaseQuery`.
- Use cases return DTOs, not entities or raw repository results.
- DTOs live in `core/<scope>/dtos` and subclass `BaseDTO`.
- Services stay focused, end with `Service`, and do not open unit-of-work
  scopes.
- Query use cases must not call repository mutators.
- Use cases that touch persistence inject `UnitOfWorkManager`, open at most one
  UoW scope, and must not inject active UoWs or providers.
- Only `ioc/container.py`, top-level delivery app/factory code, and tests may
  use `diwire.Container`.
- Use `Injected[...]` for collaborators.
- Non-foundation source classes need explicit foundation/category bases,
  matching suffixes, and scoped docstrings with concrete `Example:` blocks.
- Prefer `@dataclass(kw_only=True, slots=True)` for non-Pydantic services, use
  cases, controllers, factories, adapters, entities, and similar classes.
- Keep all `__init__.py` files empty.

## Tests

- Unit tests cover core services/use cases without FastAPI, SQLAlchemy sessions,
  or real IO.
- Integration tests cover FastAPI routes, container resolution, SQLAlchemy UoW
  behavior, and Alembic migrations.
- Architecture tests are part of the contract; update them only for intentional
  architecture changes.
- DB tests should use temp `DATABASE_URL` values and Alembic `upgrade head`.

## Migrations

- Do not use `create_all()` or `drop_all()` in source or tests.
- Add model modules under the SQLAlchemy model package; Alembic discovers them
  from `core/*/infrastructure/sqlalchemy/models`.
- Generate revisions with `make makemigrations`, review them, then run
  `make migration-check`.
- Preserve naming conventions from `BaseSQLAlchemyModel.metadata`.

## Do Not Touch Without Explicit Request

- Do not hand-edit `uv.lock`; use `uv`.
- Do not rewrite `foundation/` base classes for feature work.
- Do not move route paths into router prefixes.
- Do not bypass the DI container by constructing production graphs in delivery.
- Do not edit existing migration revisions casually; add a new revision for
  schema changes.
