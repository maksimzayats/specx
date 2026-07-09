---
name: specx-foundation
description: Use Specx foundation bases in Python services, or add a tiny project-local `foundation/` base for missing categories or stateful framework bases.
---

# Specx Foundation

Use this skill when a service class needs an explicit base, or when a new class
category may need a project-local foundation base. Read
`references/foundation.md` before editing foundation-related code.

## Workflow

1. Prefer packaged scoped bases from `specx.core.foundation`,
   `specx.delivery.foundation`, and `specx.infrastructure.foundation`.
2. Do not create an empty `src/<package>/foundation/` package.
3. Add a project-local `foundation/` module only when current code needs a real
   project-local base category or a stateful framework base that must not be
   shared globally, such as a SQLAlchemy declarative base.
4. Keep project-local foundation tiny: marker bases, common external base
   wrappers, justified ABCs, stateful framework bases, and stable cross-layer
   primitives only.
5. Give any project-local base a docstring that explains what it protects and
   includes a concrete usage example.
6. Make every non-foundation project class inherit an explicit scoped base.
7. Name each class with the suffix implied by its base ancestry, such as
   `TaskDTO`, `TaskEntity`, `TaskResponseSchema`, `CreateTaskUseCase`, or
   `TaskTitleNormalizerService`.
8. Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
   queries, DTOs, entities, and other core data classes unless the user asks for
   another model type.
9. Keep `BaseCommand` and `BaseQuery` as use-case input bases, independent from
   `BaseDTO`. Commands and queries are not result DTOs.
10. When an application value has a limited known set, model it with
   `BaseStrEnum` instead of plain `str` or `Literal[...]`.
11. Keep business rules, delivery behavior, adapter code, and runtime wiring out
   of project-local foundation modules.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/foundation.md` - packaged base catalog, import paths, extension
  rules, and architecture guardrails.
