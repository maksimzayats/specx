---
name: specx-diwire-composition
description: Wire dependency injection for a Specx Python service with `diwire`. Use when adding `ioc/container.py`, explicit dependency registrations, `Injected[...]` constructor fields, FastAPI app factory composition, test overrides, or rules that keep containers out of core use cases and services.
---

# Specx Diwire Composition

Use this skill whenever object graphs, factories, controllers, adapters, or test
overrides need `diwire`. Read `references/diwire.md` before writing DI code.

## Rules

- Application classes receive dependencies through constructor fields typed as
  `Injected[DependencyType]`.
- Only `ioc/`, top-level delivery app/factory modules, and tests create or use
  `diwire.Container`.
- Do not inject `Container`.
- Do not call `container.resolve()` inside core use cases or services.
- Let `diwire` auto-wire concrete project classes.
- Register only abstractions, external adapter bindings, factories, and
  instances that auto-wiring cannot infer. Keep registration in private
  `_register_dependencies(...)` inside `ioc/container.py`.
- Register unit-of-work managers for UoW abstractions. Persistence use cases
  inject the manager and open the active UoW inside `execute(...)`; do not
  inject `Provider[UnitOfWork]`.
- Override dependencies in tests before resolving the graph.

## References

- `references/diwire.md` - container code, registration examples, controller
  composition, and test override patterns.
