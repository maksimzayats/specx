---
name: specx-foundation
description: Use Specx foundation bases in Python services, or add a tiny project-local `foundation/` base only when the packaged bases do not cover a real class category.
---

# Specx Foundation

Use this skill when a service class needs an explicit base, or when a new class
category may need a project-local foundation base. Read
`references/foundation.md` before editing foundation-related code.

## Workflow

1. Prefer packaged bases from `specx.foundation`, for example
   `specx.foundation.dto.BaseDTO`, `specx.foundation.use_case.BaseUseCase`, and
   `specx.foundation.pure_service.BasePureService`.
2. Do not create `src/<package>/foundation/` for bases that already exist in
   `specx.foundation`.
3. Add a project-local `foundation/` module only when a real class category is
   missing from `specx.foundation` and current code needs that category.
4. Keep project-local foundation tiny: marker bases, common external base
   wrappers, justified ABCs, and stable cross-layer primitives only.
5. Give any project-local base a docstring that explains what it protects and
   includes a concrete usage example.
6. Make every non-foundation project class inherit an explicit base, usually
   from `specx.foundation`.
7. Name each class with the suffix implied by its base ancestry, such as
   `TaskDTO`, `TaskEntity`, `TaskResponseSchema`, `CreateTaskUseCase`, or
   `TaskTitleNormalizerService`.
8. Prefer `@dataclass(frozen=True, kw_only=True, slots=True)` for commands,
   queries, DTOs, entities, and other core data classes unless the user asks for
   another model type.
9. Keep business rules, delivery behavior, adapter code, and runtime wiring out
   of project-local foundation modules.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/foundation.md` - packaged base catalog, import paths, extension
  rules, and architecture guardrails.
