# Specx

**Codex skills for building Python services with explicit architectural boundaries.**

Specx is a skill catalog for generating and evolving backend services that keep
application code readable under agent-driven development. It gives Codex a
shared vocabulary for packaged foundation bases, scoped core packages, delivery
adapters, unit-of-work lifecycles, dependency injection, migrations, and
architecture tests.

[Install](#install) ·
[Skills](#skills) ·
[Generated Architecture](#generated-architecture) ·
[Contribute](CONTRIBUTING.md)

## Key Features

- **Skill-based service scaffolding.** Specx replaces a one-off code template
  with composable skills for project structure, foundation usage, tooling,
  DI, use cases, services, delivery controllers, infrastructure adapters,
  settings, migrations, and tests.
- **Explicit class boundaries.** Generated services use class-based use cases,
  services, controllers, repositories, gateways, capabilities, DTOs, entities,
  units of work, and factories with packaged `specx.foundation` bases.
- **Clear transaction ownership.** Use cases open `UnitOfWorkManager` scopes.
  Read/effect services may use an active UoW passed by the use case, but they do
  not own transaction lifecycle.
- **Guardrails for agent work.** The `specx` Python package ships rule-based
  architecture tests that reject layer leaks, entity returns from use cases,
  schema bootstrap calls, bare classes, wrong suffixes, and hidden transaction
  ownership.
- **Reusable runtime bases.** Generated services import small base classes from
  `specx.foundation` instead of vendoring a foundation tree. Projects add
  local `foundation/` modules only when a real missing category needs one.
- **Alembic-first persistence.** SQLAlchemy projects use real Alembic
  migrations and drift checks instead of `metadata.create_all()` bootstraps.

## Install

Install every Specx skill for Codex:

```sh
npx skills add maksimzayats/specx --skill '*' --agent codex -y
```

List skills from a local checkout:

```sh
npx skills add . --list --full-depth
```

Validate the catalog:

```sh
make check
```

Use the architecture package from generated projects:

```python
from pathlib import Path

from specx.testing.architecture import SpecxArchitectureConfig, assert_specx_architecture


def test_specx_architecture() -> None:
    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[2],
            package_name="order_service",
        )
    )
```

## What You Get

- A reusable Codex skill catalog under `skills/`.
- A typed Python guardrail package under `src/specx/`.
- A generated reference service under `samples/task-db-service/`.
- Rule-based architecture guardrails exposed through
  `specx.testing.architecture`.
- A compatibility renderer that writes the tiny generated-project pytest
  wrapper with the correct package name.
- Root `AGENTS.md` guidance for agents working on this catalog.
- Generated-project `AGENTS.md` guidance that projects should carry with them.

## Skills

- `specx-project-structure` creates the initial `core`, `delivery`,
  `infrastructure`, `ioc`, optional local `foundation`, optional `shared`,
  migrations, tests, and generated-project agent instructions.
- `specx-foundation` teaches packaged base usage and project-local extensions
  for real missing base categories.
- `specx-project-tooling` adds `uv`, Ruff, mypy, pytest, Makefile targets, and
  local validation commands.
- `specx-component-architecture` decides where code belongs across scopes,
  boundaries, capabilities, gateways, DTOs, schemas, adapters, and shared code.
- `specx-diwire-composition` wires `diwire.Container`, `Injected[...]`, private
  registrations, app factories, and test overrides.
- `specx-add-core-use-case` adds command/query-driven use cases that return
  DTOs and own UoW scopes when persistence is needed.
- `specx-add-core-service` adds focused reusable core behavior without hiding
  transaction lifecycle.
- `specx-add-infrastructure-adapter` adds repositories, gateways, UoW
  implementations, SQLAlchemy, Redis, HTTP, SDK, and other technical adapters.
- `specx-sqlalchemy-migrations` adds async Alembic configuration, revisions,
  migration commands, and drift tests.
- `specx-add-delivery-controller` adds top-level FastAPI controllers, schemas,
  route registration, and delivery-only helpers.
- `specx-settings` adds `pydantic-settings` configuration without direct
  environment reads in core code.
- `specx-tests` adds unit, integration, end-to-end, DI, migration, and
  architecture tests backed by the `specx` package.

## Generated Architecture

Specx projects import foundation bases from `specx.foundation` and organize
application code around scoped core packages:

```text
src/<package>/
  core/
    <scope>/
      capabilities/
      dtos/
      entities/
      exceptions/
      gateways/
      repositories/
      services/
      use_cases/
      infrastructure/
  delivery/
    fastapi/
      __main__.py
      factory.py
      controllers/
      schemas/
      services/
  infrastructure/
  ioc/
  shared/
migrations/
```

`core/<scope>/delivery/` is intentionally not part of the structure. Delivery
lives at the top level, while core packages stay framework-free.

Create `src/<package>/foundation/` only when a real class category is missing
from `specx.foundation`. Local foundation module filenames are not
`base_`-prefixed, but class names stay prefixed, for example `clock.py` defines
`BaseClock`.

## Core Rules

- Every project class inherits an explicit packaged or project-local foundation
  base.
- Use cases accept exactly one same-file `Command` or `Query` and return DTOs,
  not entities.
- Commands represent state-changing operations. Queries are read-only, even
  when the input is empty.
- Commands, queries, DTOs, entities, and other core data classes should use
  `@dataclass(frozen=True, kw_only=True, slots=True)` unless the user asks for
  another model type. Keep Pydantic for delivery schemas and settings.
- Core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`; do not add a generic `BaseService`.
- Small injectable collaborators inherit `BaseCapability`, live under
  `core/<scope>/capabilities/`, and do not pretend to be services,
  repositories, gateways, helpers, or managers.
- Gateway ports inherit `BaseGateway`, live under `core/<scope>/gateways/`,
  declare external effects, use business language, and do not return entities.
- Persistence use cases inject a `UnitOfWorkManager` and open an active
  `UnitOfWork` inside `execute(...)`.
- Services may receive an active UoW as a method argument, but they do not open
  UoW scopes, commit, or roll back.
- SQLAlchemy schema is managed by Alembic migrations, not application schema
  bootstrap calls.
- `diwire.Container` belongs in `ioc`, top-level delivery factory/entrypoint
  code, and tests only.

## Reference Service

The sample service under `samples/task-db-service/` is a working generated
project used to validate the skills. It includes:

- FastAPI delivery with `task_db_service.delivery.fastapi.__main__:app`.
- Task use cases with command/query inputs and DTO outputs.
- Split pure/read/effect services.
- SQLAlchemy repositories and UoW manager.
- Alembic migrations and drift checks.
- Architecture tests that call the rule-based `specx` guardrail package.

Run it from the sample directory:

```sh
cd samples/task-db-service
make check
```

## Contributing

Developer setup, architecture notes, sample regeneration expectations, and
validation workflow live in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Specx is released under the [MIT License](LICENSE.md).
