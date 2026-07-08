# Specx Skills

Install from this repo with:

```bash
npx skills add maksimzayats/specx --skill '*' --agent codex -y
```

List locally before installing:

```bash
npx skills add . --list --full-depth
```

Validate the catalog:

```bash
make check
```

## new:

```text
AGENTS.md                     # coding-agent project instructions
src/<package>/
  foundation/
    command.py               # base for state-changing use-case inputs
    dto.py                   # base for result payloads
    entity.py                # base for framework-free state
    exceptions.py            # application exception bases
    factory.py               # base for app/client/session factories
    repository.py            # base for repository ports
    service.py               # base for core services
    settings.py              # base for pydantic-settings classes
    query.py                 # base for read-only use-case inputs
    unit_of_work.py          # base for active UoW contracts
    unit_of_work_manager.py  # base for UoW lifecycle managers
    use_case.py              # base for application actions
    delivery/
      controller.py          # base for delivery controllers
      service.py             # base for auth/rate-limit/request helpers
      fastapi/schema.py      # base for FastAPI schemas
    infrastructure/
      sqlalchemy/model.py    # base for SQLAlchemy models
  core/
    <scope>/                  # application/domain boundary, e.g. tasks
      dtos/                   # use-case result DTOs
      entities/               # framework-free state
      exceptions/             # application errors
      repositories/           # ports/contracts for external IO
      services/               # reusable core behavior
      use_cases/              # externally meaningful actions
      infrastructure/         # scope-owned DB/Redis/HTTP adapters, if needed
  delivery/
    fastapi/
      app.py                  # runtime import target
      factory.py              # app composition/lifespan
      controllers/            # one controller per scoped use-case set
      schemas/                # request/response models
      services/               # auth/rate-limit/request helpers, if needed
  infrastructure/              # shared technical resources
    sqlalchemy/                # app-wide engine/session/settings, if needed
  ioc/                        # diwire container and private registrations
  shared/                     # optional stable cross-scope primitives
migrations/                    # Alembic migration environment, if SQL exists
```

`core/<scope>/delivery/` is intentionally not part of the structure. Delivery
logic lives in top-level `delivery/`.
Every non-foundation class should inherit an explicit base and use the suffix
implied by foundation base ancestry: `Command`, `Query`, `DTO`, `Entity`,
`Schema`, `Service`, `Repository`, `UnitOfWork`, `UnitOfWorkManager`, `UseCase`,
`Controller`, `Factory`, `Settings`, `Enum`, `Model`, etc. Major classes should
include a docstring that explains the class scope and shows a concrete
`Example:`. Use case inputs are same-file `Command` or `Query` classes:
commands are state-changing, queries are read-only, and empty inputs are still
explicit. Use cases return DTOs, not entities. Persistence use cases inject a
`UnitOfWorkManager` and open an active `UnitOfWork` inside `execute(...)`; do
not inject `Provider[UnitOfWork]`. Deterministic use cases with no external IO
do not need a UoW. Add a new foundation base only when a real class category
exists and no current base fits. SQLAlchemy projects use Alembic migrations, not
`metadata.create_all` application bootstraps.

## Skills

- `specx-project-structure` - Create the `core`, `delivery`, `ioc`, optional `shared`, and test roots.
- `specx-foundation` - Add explicit base classes and guardrails for project class inheritance.
- `specx-project-tooling` - Set up `uv`, Ruff, mypy, pytest, Makefile targets, and local checks.
- `specx-diwire-composition` - Wire `diwire.Container`, `Injected[...]`, private registrations, and overrides.

- `specx-component-architecture` - Define scope boundaries, import rules, DTO/schema placement, and shared conventions.
- `specx-add-core-use-case` - Add one application action with `execute(...)`, DTOs, services, and UoW ownership.
- `specx-add-core-service` - Add focused reusable core behavior without transaction ownership.
- `specx-add-infrastructure-adapter` - Add DB, Redis, network, repository, or UoW adapters for core ports.
- `specx-sqlalchemy-migrations` - Add async Alembic config, revisions, commands, and migration tests.
- `specx-add-delivery-controller` - Add FastAPI controllers, schemas, and delivery-only helpers.

- `specx-settings` - Add focused `pydantic-settings` classes and inject config instead of reading env in core.
- `specx-tests` - Add unit, integration, e2e, and architecture tests for behavior, wiring, and boundaries.
