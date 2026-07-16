# Specx

**Agent skills for building Python services with explicit architectural boundaries.**

Specx is a skill catalog for generating and evolving backend services that keep
application code readable under agent-driven development. It gives AI coding
agents a shared vocabulary for packaged foundation bases, scoped core packages,
delivery adapters, unit-of-work lifecycles, dependency injection, migrations,
and architecture tests.

[Install](#install) ·
[Skills](#skills) ·
[Documentation](#documentation) ·
[Generated Architecture](#generated-architecture) ·
[Contribute](CONTRIBUTING.md)

## Key Features

- **Neutral project initialization.** `specx init` creates a strict, immediately
  checkable Python project with a small framework-neutral `core/health` use
  case and service, DI composition, and mirrored unit tests. Composable skills
  then add delivery, infrastructure, settings, migrations, and real scopes.
- **Explicit class boundaries.** Generated services use class-based use cases,
  services, controllers, repositories, gateways, capabilities, DTOs, entities,
  units of work, and factories with packaged scoped foundation bases.
- **Clear transaction ownership.** Use cases open `UnitOfWorkManager` scopes
  and do not inject repositories, SQLAlchemy sessions, engines, session
  factories, or concrete infrastructure adapters directly. Read/effect services
  may use an active UoW passed by the use case, but they do not own transaction
  lifecycle.
- **Guardrails for agent work.** The `specx` Python package ships rule-based
  architecture checks that reject layer leaks, entity returns from use cases,
  schema bootstrap calls, bare classes, wrong suffixes, and hidden transaction
  ownership. The `specx` CLI gives humans and coding agents the same fast,
  deterministic feedback loop.
- **Standard runtime logging.** Generated API services configure Python stdlib
  logging once through top-level infrastructure and keep logger creation local
  to classes that actually emit log records.
- **Explicit FastAPI lifespans.** Generated FastAPI apps inject a
  `FastAPILifecycle` into the app factory, pass it to `FastAPI(lifespan=...)`,
  and close app-owned resources plus the DI container during shutdown.
- **Explicit foundation boundaries.** Generated services import stateless base
  classes from `specx.core.foundation`, `specx.delivery.foundation`, and
  `specx.infrastructure.foundation` instead of vendoring a foundation tree.
  They add local `foundation/` modules only for real project-local categories
  or stateful framework bases such as a SQLAlchemy declarative base.
- **Container-centric tests.** Generated tests use native pytest `container`
  fixtures and direct `container.resolve(Target)` calls. Overrides are
  registered before resolution, one-off class-based doubles live in the
  `test_*.py` module that uses them, reused unit-test doubles live in mirrored
  `fake_<source_module>.py` files under unit `capabilities`, `gateways`, or
  `repositories` test packages, and generated tests mirror source modules with
  flat paths such as
  `tests/unit/core/tasks/services/test_title_service.py`.
- **Alembic-first persistence.** SQLAlchemy projects use real Alembic
  migrations and drift checks instead of `metadata.create_all()` bootstraps.

## Install

Install every Specx skill for your target agent. For the `codex` target:

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

Initialize a new framework-neutral project:

```sh
uvx specx init order-service
cd order-service
make check
```

`specx init [PATH]` derives a kebab-case distribution name and underscore import
package from the target directory and targets Python 3.14. It runs
`uv add specx diwire` followed by `uv add --dev mypy pytest ruff`, allowing uv to
select and record every initial dependency version while creating the lockfile
and environment. Use `--name`, `--package`, or `--python` to override the
generated metadata, or `--no-sync` to render without adding dependencies.
Initialization accepts only a new, empty, or `.git`-only target and never
overwrites an existing project. `--python` accepts any `major.minor` value, so
new Python releases do not require a Specx update to initialize a project.

The generated baseline contains packaging, strict Ruff/mypy/pytest tooling,
`AGENTS.md`, a health DTO/enum/service/use case, `ioc/container.py`, and mirrored
unit tests. It does not create delivery,
infrastructure, FastAPI, or empty future-facing
directories. Both Specx and Ruff start with `select = ["ALL"]`; every Ruff
formatter or file-category exception is documented inline in `pyproject.toml`.

Add the Python package to existing projects, then run the guardrail CLI:

```sh
uv add specx
uv run specx check
uv run specx rule list
uv run specx rule explain use-cases.return-dtos
```

`specx check` discovers the single importable package under `src/` and runs all
framework-neutral rules by default. Configure overrides and opt-in technology
families in `pyproject.toml`:

```toml
[tool.specx]
select = ["ALL"]
ignore = ["delivery.routes-use-full-api-v1-paths"]
exclude = ["src/order_service/generated/**"]
```

`select` replaces the default framework-neutral selection and accepts `ALL`,
semantic rule IDs, or rule families. `extend-select` adds selectors. With
`ALL`, rules requiring a technology surface run when that surface exists;
missing surfaces are skipped without warnings. Explicitly selecting a missing
technology family still emits a warning.

Use `--output-format json` for agent and CI integrations. Warnings do not fail
the command; architecture violations exit with status 1, while configuration
or execution errors exit with status 2.

The typed Python API remains available for programmatic checks and custom
rules:

```python
from pathlib import Path

from specx.testing.architecture import SpecxArchitectureConfig, assert_specx_architecture


def test_specx_architecture() -> None:
    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[3],
            package_name="order_service",
            extend_select=frozenset({"fastapi"}),
        )
    )
```

## Documentation

The documentation site follows the same Storybook, React/Vite, MDX, and GitHub
Pages approach used by OpenAI's Apps SDK UI documentation. Run it locally with:

```sh
npm --prefix docs ci
make docs
```

Create the static production build with `make docs-build`. Pushes to `main`
publish that build through the repository's configured GitHub Pages domain.

## What You Get

- A reusable agent skill catalog under `skills/`.
- A typed Python guardrail package under `src/specx/`.
- A safe `specx init` command for fresh framework-neutral Python projects.
- Rule-based architecture guardrails exposed through
  `specx.testing.architecture`.
- A `specx check` CLI with semantic rule IDs, rule-family selection, and JSON
  diagnostics.
- A compatibility renderer that writes the tiny generated-project pytest
  wrapper with the correct package name.
- Root `AGENTS.md` guidance for agents working on this catalog.
- Generated-project `AGENTS.md` guidance that projects should carry with them.

## Skills

- `specx-project-structure` creates the initial `core`, `delivery`,
  `infrastructure`, `ioc`, optional local `foundation`, optional `shared`,
  migrations, tests, and generated-project agent instructions.
- `specx-foundation` teaches packaged stateless base usage and project-local
  extensions for real missing base categories or stateful framework bases.
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
  implementations, SQLAlchemy, Redis, HTTP, SDK, logging configurators, and
  other technical adapters.
- `specx-sqlalchemy-migrations` adds async Alembic configuration, revisions,
  migration commands, and drift tests.
- `specx-add-delivery-controller` adds top-level FastAPI controllers, schemas,
  route registration, delivery lifecycles, and delivery-only helpers.
- `specx-settings` adds `pydantic-settings` configuration without direct
  environment reads in core code.
- `specx-tests` adds unit, integration, end-to-end, DI, migration, and
  architecture tests backed by the `specx` package.

## Generated Architecture

Specx projects import stateless foundation bases from scoped Specx packages and
organize application code around scoped core packages:

```text
src/<package>/
  foundation/  # only when project-local/stateful bases are needed
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
      lifecycle.py
      controllers/
      schemas/
      services/
  infrastructure/
    logging/
  ioc/
  shared/
migrations/
```

`core/<scope>/delivery/` is intentionally not part of the structure. Delivery
lives at the top level, while core packages stay framework-free.

Do not create an empty local `foundation/` package. `specx.core.foundation`,
`specx.delivery.foundation`, and `specx.infrastructure.foundation` are the
default scoped foundation boundaries. Create
`src/<package>/foundation/` only for project-local base categories or stateful
framework bases that must not be shared globally, such as the project
SQLAlchemy declarative base. Local foundation module filenames are not
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
  `UnitOfWork` inside `execute(...)`. They do not inject repositories,
  SQLAlchemy sessions/engines/session factories, or concrete infrastructure
  adapters directly.
- Services may receive an active UoW as a method argument, but they do not open
  UoW scopes, commit, or roll back.
- SQLAlchemy schema is managed by Alembic migrations, not application schema
  bootstrap calls.
- Runtime logging is configured once in top-level infrastructure. Do not inject
  `logging.Logger` or register loggers in `diwire.Container`; classes that
  actually log create private stdlib class loggers.
- FastAPI lifespan lives in `delivery/fastapi/lifecycle.py`, inherits
  `BaseLifecycle[FastAPI]`, closes app-owned infrastructure resources, then
  calls `container.aclose()` on shutdown. It must not run migrations or schema
  creation.
- `diwire.Container` belongs in `ioc`, top-level delivery
  factory/entrypoint/lifecycle code, and tests only. `Injected[Container]` is
  allowed only in `FastAPILifecycle`.

## Contributing

Developer setup, architecture notes, sample regeneration expectations, and
validation workflow live in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Specx is released under the [MIT License](LICENSE.md).
