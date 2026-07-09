---
name: specx-diwire-composition
description: Wire dependency injection for a Specx Python service with `diwire`. Use when adding `ioc/container.py`, explicit dependency registrations for capabilities, repositories, gateways, UoW managers, clients, settings, or factories, `Injected[...]` constructor fields, FastAPI app factory composition, test overrides, or rules that keep containers out of core use cases and services.
---

# Specx Diwire Composition

Use this skill whenever object graphs, factories, controllers, adapters, or test
overrides need `diwire`. Read `references/diwire.md` before writing DI code.

## Rules

- Application classes receive dependencies through constructor fields typed as
  `Injected[DependencyType]`.
- Capabilities are normal injectable collaborators. Register only capability
  abstractions or existing instances that auto-wiring cannot infer.
- Only `ioc/`, top-level delivery `__main__.py`/factory modules, and tests
  create or use `diwire.Container`.
- Do not inject `Container`.
- Do not inject `logging.Logger` or register loggers in the container. Runtime
  logging is configured once by a top-level infrastructure configurator; classes
  that log create local stdlib loggers.
- Do not call `container.resolve()` inside core use cases or services.
- Let `diwire` auto-wire concrete project classes.
- Register only abstractions, external adapter bindings, gateway
  implementations, factories, and instances that auto-wiring cannot infer.
  Keep registration in private `_register_dependencies(...)` inside
  `ioc/container.py`.
- Register concrete gateway implementations for their core `BaseGateway` ports.
- Register health readiness gateway implementations, such as
  `SQLAlchemyReadinessCheckGateway`, for `ReadinessCheckGateway` when
  `/readyz` needs infrastructure checks.
- Register unit-of-work managers for UoW abstractions. Persistence use cases
  inject the manager and open the active UoW inside `execute(...)`; they do not
  inject repositories, active UoWs, providers, SQLAlchemy sessions, engines,
  session factories, or concrete infrastructure adapters directly.
- Unit tests receive a fresh native pytest `container` fixture. Register
  scenario-specific overrides directly in the test before resolving the target.
- Integration tests receive the transactional real-app `container` fixture.
  They must use the real internal graph; do not mock internal use cases,
  services, or capabilities.
- Use `container.resolve(...)` for normal synchronous graph construction, even
  for targets with async methods; use `await container.aresolve(...)` only when
  DI construction itself has async providers.
- One-off class-based test doubles live in the `test_*.py` module that uses
  them. Reused unit-test doubles may live in mirrored
  `tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
  modules.
- Inline `MagicMock` or `AsyncMock` in the test function when only one behavior
  needs to change.
- Do not create DI-backed test factories, target harnesses, `harness.py`,
  `tests/_support/fakes`, `tests/**/_fakes.py`, or fake modules outside
  those mirrored unit port/capability packages.
- Keep tests on native pytest fixtures. Do not enable
  `diwire.integrations.pytest_plugin`, and do not use `Injected[...]`
  parameters in test functions.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/diwire.md` - container code, registration examples, controller
  composition, and test override patterns.
