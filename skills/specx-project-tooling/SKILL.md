---
name: specx-project-tooling
description: Add strict Python project tooling for a Specx service. Use when creating or updating `pyproject.toml`, `uv` dependency groups and lock checks, Ruff formatting and linting, mypy strict mode, pytest and HTTPX2 test configuration, Makefile commands, root `AGENTS.md` command guidance, or CI-like local guardrails.
---

# Specx Project Tooling

Use this skill to make the repository executable and checkable. Read
`references/tooling.md` before editing tooling files.

## Workflow

1. Use `specx init <path>` for the fresh framework-neutral baseline. It renders
   the canonical `pyproject.toml`, Makefile, `.python-version`, health core/IOC
   scaffold, mirrored unit tests, and root guidance, then runs
   `uv add specx diwire` and
   `uv add --dev mypy pytest ruff` unless `--no-sync` is passed. Let uv select
   and record compatible releases rather than rendering dependency floors.
2. Preserve the repo's Python version if it already exists. For a new repo,
   default to Python 3.14. The initializer accepts any `major.minor` value;
   do not hardcode a release allowlist that blocks future Python versions.
3. Use `uv` metadata in `pyproject.toml`.
4. For a new project, verify current compatible releases against the official
   package indexes and documentation before copying reference floors. Preserve
   intentional versions in an existing repo unless the user asks to upgrade.
5. Add runtime dependencies only for real runtime features. For a starter API,
   include `specx`, FastAPI, `diwire`, `pydantic-settings`, and Uvicorn.
6. Add dev dependencies for pytest, Ruff, mypy, HTTP testing, and ASGI lifespan
   testing when there is a FastAPI app.
7. Keep mypy strict. Do not enable the DIWire mypy plugin for constructor-field
   injection; it is only needed if an existing project intentionally uses
   `resolver_context.inject` function wrappers.
8. Enable `select = ["ALL"]` for Ruff in new projects. Ignore only formatter
   conflicts and deliberate file-category conventions, and put a concise
   comment describing what each ignored rule checks beside its code.
9. Generate `[tool.specx]` with `select = ["ALL"]` so every applicable built-in
   guardrail is explicit. Missing technology surfaces are skipped for `ALL`;
   explicit technology selectors still warn when their surface is absent.
10. Add simple Makefile targets: `check`, `format`, `lint`, `test`, and `dev`
   when there is a FastAPI delivery app. `lint` runs Ruff, mypy, and
   `uv run --locked specx check`; do not create separate `guardrails` or
   `lock-check` targets.
11. If SQLAlchemy adapters exist, add Alembic dependency/config and
   `migrate`/`makemigrations` targets with `$specx-sqlalchemy-migrations`.
12. When adding or changing Makefile targets, update root `AGENTS.md` Commands
   so coding agents run the right project commands.
13. Use locked execution for non-mutating validation commands.
14. Run the smallest useful checks after changing tooling.

## Guardrails

- Do not add heavyweight services such as Docker, Alembic, Redis, or
  PostgreSQL unless the repo has code that uses them.
- Once a SQLAlchemy adapter exists, Alembic is required. Do not use
  `metadata.create_all` as a replacement for migrations.
- Do not split linting rules across many files unless the project already does.
- Keep commands copyable and non-interactive.
- Keep `AGENTS.md` command guidance aligned with the actual Makefile. Do not
  list migration commands before SQLAlchemy/Alembic exists.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/tooling.md` - recommended `pyproject.toml`, Makefile, and command
  patterns.
