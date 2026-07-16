# Contributing

Specx is an agent skill catalog plus a typed Python guardrail package. Changes
usually touch the package and the skills together so future agents learn the
same architecture that the guardrails enforce.

## Repository Layout

```text
skills/                         # published agent skills
  specx-*/SKILL.md              # trigger metadata and workflow
  specx-*/references/*.md       # detailed generation guidance
.agents/skills/                 # tracked local-discovery mirror
src/specx/                      # reusable architecture guardrail package
tests/                          # package and skill-helper tests
scripts/validate_skills.py      # skill metadata validator
AGENTS.md                       # instructions for agents editing this repo
README.md                       # user-facing catalog overview
```

## Prerequisites

- Node.js with `npx`, for `skills add`.
- `uv`, for Python validation commands.
- Python available through `uv`.

## Root Commands

Validate the Python package, skill catalog, and installable skill list:

```sh
make check
```

Run package checks individually:

```sh
make lint
make type
make test
make build
```

Validate skill metadata only:

```sh
make validate-skills
```

Synchronize the tracked local-discovery mirror after editing canonical skills:

```sh
make sync-skills
```

List local skills:

```sh
make list-skills
```

## Skill Authoring

Each skill has:

- `SKILL.md` with YAML frontmatter containing only `name` and `description`.
- Optional `references/*.md` files for detailed instructions and examples.
- Optional `agents/openai.yaml` metadata when the skill is meant to surface in
  skill UI lists.

Keep `SKILL.md` concise and trigger-oriented. Put reusable patterns, examples,
and guardrail details in `references/`. Do not add README-style files inside
individual skill folders. Add a compact linked `## Contents` section to
Markdown references over 100 lines. Edit only canonical `skills/`, then run
`make sync-skills`; `make validate-skills` rejects mirror drift.

When changing a rule:

1. Update the skill that teaches the rule.
2. Update cross-cutting references that repeat the rule.
3. Update `AGENTS.md` if agents need the rule before loading a skill.
4. Update the package rule and focused tests when enforcement changes.
5. Run root `make check` and forward-test substantial generation changes in a
   disposable project when practical.

## Architecture Contract

Generated services should preserve these boundaries:

- Scoped Specx foundation packages define the default reusable base classes for
  generated services: `specx.core.foundation`, `specx.delivery.foundation`,
  and `specx.infrastructure.foundation`.
- `foundation/`, when present in a generated service, contains only
  project-local base classes missing from the scoped foundation packages.
- `core/<scope>/` contains framework-free application behavior.
- `delivery/` contains framework adapters, controllers, schemas, app lifecycle
  managers, and delivery-only helpers.
- `core/<scope>/infrastructure/` contains scope-owned technical adapters.
- top-level `infrastructure/` contains app-wide technical resources, including
  process-wide logging configuration.
- `ioc/` owns `diwire.Container` composition.
- FastAPI lifecycle code closes app-owned infrastructure resources and is the
  only generated class allowed to inject `diwire.Container`.
- `shared/` is optional and only for stable cross-scope primitives.

Project-local foundation module filenames are intentionally unprefixed:

```text
foundation/clock.py
foundation/generator.py
```

Foundation class names stay prefixed:

```python
class BaseClock: ...
class BaseGenerator: ...
```

## Use Cases, Services, And UoW

Use cases are externally meaningful actions. Each `execute(...)` method accepts
exactly one same-file input:

- `Command` for side-effecting operations.
- `Query` for read-only operations.

Use cases return DTOs, not entities or raw repository results.
Commands, queries, DTOs, entities, and other core data classes should use
`@dataclass(frozen=True, kw_only=True, slots=True)` unless a user explicitly
asks for another model type. Keep Pydantic at delivery schemas and settings
edges.

Persistence use cases inject a `UnitOfWorkManager` and open the active
`UnitOfWork` inside `execute(...)`. Services may accept that active UoW as a
method argument, but services must not open UoW scopes or own commit/rollback.

Core services use one of:

- `BasePureService` for deterministic helpers with no IO or runtime state.
- `BaseReadService` for read-only orchestration.
- `BaseEffectService` for side-effecting helpers that operate inside a use-case
  owned UoW or call effect gateways.

Do not add a generic `BaseService`.

## Repositories, Gateways, And Capabilities

Use repositories for owned persistence. Repositories may return entities inside
core boundaries.

Use top-level logging configurators for runtime logging setup. Do not inject
`logging.Logger` or register loggers in the container; classes that actually
log create private stdlib class loggers.

Use gateways for outbound business capabilities provided by external systems:
OpenAI, payments, email, queues, external HTTP APIs, and similar dependencies.
Gateway ports inherit `BaseGateway`, live under `core/<scope>/gateways/`,
declare external effects in docstrings, and do not return entities.

Use capabilities for small injectable collaborators that are narrower than
services. Direct subclasses of `BaseCapability` end with `Capability`. If a
capability family becomes common or needs stronger checks, introduce a narrower
project-local foundation base such as `BaseClock` or `BaseGenerator`.

## Architecture Guardrails

Rule-based guardrails live in the `specx` Python package. Each built-in
architecture check is a concrete `*Rule` subclass with a stable
`SpecxRuleId` and a useful docstring explaining the rule.

Generated projects should keep a tiny pytest wrapper:

```python
from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    assert_specx_architecture,
)


def test_specx_architecture() -> None:
    disabled_rules: frozenset[SpecxRuleId] = frozenset()

    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[3],
            package_name="url_shortener_service",
            disabled_rules=disabled_rules,
        )
    )
```

The compatibility renderer writes that wrapper for existing workflows:

```sh
python3 skills/specx-tests/references/render_architecture_guardrails.py \
  --package url_shortener_service \
  --output /path/to/service/tests/guardrails/architecture/test_boundaries.py
```

When changing guardrail behavior, update the package rule, its focused tests,
the compatibility renderer if needed, and any skill docs that teach the rule.

## Migrations

SQLAlchemy projects use Alembic migrations. Do not introduce source or test
code that calls `metadata.create_all()` or `drop_all()`.

Model discovery should load every SQLAlchemy model under
`core/*/infrastructure/sqlalchemy/models` so Alembic drift checks compare
against complete metadata.

## Pull Request Checklist

- Root `make check` passes.
- Substantial generated-project changes were forward-tested when practical.
- Skill references and package guardrails agree on architecture rules.
- Package architecture rules and the compatibility wrapper renderer agree.
- No placeholder folders, local copies of packaged bases, or speculative
  foundation bases were added.
- No unrelated generated caches or local environment files were committed.
