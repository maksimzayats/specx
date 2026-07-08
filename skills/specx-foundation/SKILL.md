---
name: specx-foundation
description: Add or extend the Specx foundation package for Python services. Use when creating base classes for commands, queries, DTOs, entities, capabilities, gateways, services, use cases, repositories, units of work, settings, factories, controllers, schemas, exceptions, infrastructure models, or enforcing that project classes inherit explicit foundation bases.
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
   `TaskSummaryGateway`, `CreateTaskUseCase`, and
   `TaskTitleNormalizerService`.
8. Use `BaseCapability` for small injectable collaborators that are narrower
   than services.
9. When a capability family appears more than once or needs stronger review
   rules, add a narrower foundation base that inherits `BaseCapability`, such
   as `BaseClock` or `BaseGenerator`.
10. For core services, use `BasePureService`, `BaseReadService`, or
   `BaseEffectService`. Do not add a generic `BaseService`.
11. Use `BaseGateway` for outbound business capability ports to external
   systems.
12. Do not add `base_` prefixes to foundation module filenames. Class names
    stay prefixed, for example `capability.py` defines `BaseCapability` and
    `pure_service.py` defines `BasePureService`.
13. Use existing foundation bases first.
14. Add a new foundation base only when a real new class category appears.
15. Keep business rules, delivery behavior, adapter code, and runtime wiring out
   of foundation.
16. Add architecture tests that reject bare non-foundation classes, direct raw
    bases outside foundation, suffix mismatches, and entity returns from use
    cases.

## References

- `references/foundation.md` - base class catalog, examples, extension rules,
  and architecture guardrails.
