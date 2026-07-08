---
name: specx-foundation
description: Add or extend the Specx foundation package for Python services. Use when creating base classes for commands, queries, DTOs, entities, services, use cases, repositories, units of work, settings, factories, controllers, schemas, exceptions, infrastructure models, or enforcing that project classes inherit explicit foundation bases.
---

# Specx Foundation

Use this skill when adding the base class layer for a Specx service or when a
new class category needs a justified foundation base. Read
`references/foundation.md` before editing foundation code.

## Workflow

1. Put reusable base classes under `foundation/`.
2. Keep foundation tiny: marker bases, common framework bases, justified ABCs,
   and cross-layer primitives only.
3. Use plain root classes for foundation markers and keep them minimal.
4. Give every foundation base a docstring that explains its scope and includes
   one concrete usage example.
5. Give major concrete project classes a docstring that explains class scope
   and includes a concrete `Example:` block.
6. Make every non-foundation project class inherit an explicit base class.
7. Name each class with the suffix implied by its foundation base ancestry, for
   example `TaskDTO`, `TaskEntity`, `TaskResponseSchema`,
   `CreateTaskUseCase`, and `TaskTitleNormalizerService`.
8. Use existing foundation bases first.
9. Add a new foundation base only when a real new class category appears.
10. Keep business rules, delivery behavior, adapter code, and runtime wiring out
   of foundation.
11. Add architecture tests that reject bare non-foundation classes, direct raw
    bases outside foundation, suffix mismatches, and entity returns from use
    cases.

## References

- `references/foundation.md` - base class catalog, examples, extension rules,
  and architecture guardrails.
