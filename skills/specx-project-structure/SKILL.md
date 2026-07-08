---
name: specx-project-structure
description: Create or reshape a Python service repo into the Specx clean core/delivery/foundation layout. Use when starting a new backend repo, converting a template into skills, adding the first src package, or establishing `AGENTS.md`, `foundation/`, `core/`, `delivery/`, top-level `infrastructure/`, `ioc/`, optional `shared/`, conditional migrations, and test roots for FastAPI, `diwire`, and class-based application code.
---

# Specx Project Structure

Use this skill to create the repo shell and first runnable vertical slice. For
details, read `references/blueprint.md`.

## Workflow

1. Derive the import package from the project name: lowercase, hyphen to
   underscore, valid Python identifier.
2. Create `src/<package>/` with empty `__init__.py` files only.
3. Add `foundation/` with the base classes used by the classes that exist now.
4. Use `core/<scope>/` as the main boundary. Put application packages at the
   scope root: `dtos/`, `entities/`, `exceptions/`, `repositories/`,
   `services/`, and `use_cases/`. Put scope-owned technical adapters under
   `infrastructure/` only when real IO exists.
5. Add top-level `delivery/` for runnable framework apps, controllers,
   request/response schemas, and delivery-only services.
6. Add top-level `infrastructure/` for shared technical resources such as
   SQLAlchemy session factories, logging, telemetry, and external client
   factories.
7. Add `ioc/` for `diwire.Container` creation and explicit bindings.
8. Add `shared/` only for stable cross-scope application primitives such as
   unit-of-work contracts, clocks, ids, or errors.
9. Add `migrations/` with Alembic when SQLAlchemy models exist.
10. Create a tiny health scope as the first vertical slice when the user asks
   for a new repo from scratch.
11. Create root `AGENTS.md` for every new repo. Include runnable project
   commands from `$specx-project-tooling` and Specx boundaries from
   `$specx-component-architecture`.
12. Add tests only where there is real code to test. Do not create empty folders
   just to satisfy the diagram.

## Hard Rules

- Keep `__init__.py` files empty.
- Every project class must inherit an explicit base class.
- Prefer foundation bases such as `BaseDTO`, `BaseEntity`, `BaseService`,
  `BaseCommand`, `BaseQuery`, `BaseUseCase`, `BaseRepository`, `BaseUnitOfWork`,
  `BaseUnitOfWorkManager`, `BaseController`, `BaseFastAPISchema`, and
  `BaseFactory`.
- Every major class should have a docstring that explains the class scope and
  includes a concrete `Example:`.
- Extend `foundation/` with a new base class only when a real class category
  exists and no existing base fits.
- Core application code (`dtos/`, `entities/`, `exceptions/`, `repositories/`,
  `services/`, `use_cases/`) must not import FastAPI, SQLAlchemy, Redis, HTTP
  clients, `delivery`, or the DI container.
- Do not put a `delivery/` folder under `core/<scope>/`.
- Delivery maps framework input/output and calls use cases.
- Use one controller per scoped set of use cases, for example one
  `TasksController` for create/get/list task routes.
- Put delivery-only logic such as auth dependencies, rate limiting, request
  context, and controller helpers under `delivery/`, not `core/`.
- Every class under a `services/` package must end with `Service`.
- Infrastructure contains technical IO only. No business decisions there.
- App-wide technical infrastructure must not live inside one core scope.
- SQLAlchemy schema is managed with Alembic migrations, not application
  `metadata.create_all` calls.
- `ioc/` and top-level delivery app/factory modules may import across layers to
  compose the app.
- Prefer one primary public class per file.
- Prefer class-based use cases, services, controllers, factories, and adapters.
- Prefer `@dataclass(kw_only=True, slots=True)` for non-Pydantic services, use
  cases, controllers, factories, adapters, entities, and similar classes.
- Generated projects must include root `AGENTS.md`. Keep its Commands section
  aligned with the Makefile and include only commands that exist in that
  project.

## References

- `references/blueprint.md` - target tree, starter files, and creation checklist.
