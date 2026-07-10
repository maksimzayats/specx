---
name: specx-tests
description: Add or refine tests for Specx Python services. Use when creating unit tests for use cases/services, integration tests for FastAPI controllers or infrastructure adapters, e2e smoke tests, architecture import guardrails, DI override tests, pytest fixtures, or coverage and boundary checks.
---

# Specx Tests

Use this skill when behavior, wiring, or architecture boundaries need tests.
Read `references/testing.md` before creating test files.

## Test Layers

- `tests/_support/`: generic clients, DB helpers, and shared integration
  helpers only. This is not a test suite and does not hold project-specific
  doubles.
- `tests/unit/`: core services, use cases, and capabilities resolved from a
  fresh explicit `diwire.Container`.
- `tests/integration/`: real internal graph tests. Core use-case integration
  tests call resolved use cases against the transactional DB; delivery
  integration tests exercise HTTP mapping; migrations prove Alembic behavior.
- `tests/e2e/`: optional whole-app smoke flows.
- `tests/guardrails/`: the packaged
  `specx.testing.architecture.assert_specx_architecture` wrapper plus any
  genuinely project-specific extra rules.

## Rules

- Test behavior and boundaries, not implementation ceremony.
- Required generated coverage is currently scoped to core services, use cases,
  and capabilities.
- Mirror source module paths directly with flat test files, for example
  `tests/unit/core/tasks/services/test_title_service.py`.
- Do not create per-target test folders, `harness.py`, target factories, or
  target harnesses.
- `tests/unit/conftest.py` owns the fresh bare `Container` fixture for unit
  tests. `tests/integration/conftest.py` owns the transactional DB-backed
  `container` fixture for integration tests.
- Test functions receive `container`, register any scenario-specific overrides
  before resolution, then call `container.resolve(Target)`.
- If a complete replacement is needed by every test in one module, a
  module-local `container` fixture may register it before returning the
  container.
- Keep one-off class-based test doubles in the `test_*.py` module that uses
  them. When the same double is reused by multiple unit modules, put it in a
  mirrored
  `tests/unit/core/<scope>/{capabilities,gateways,repositories}/fake_<source_module>.py`
  file.
- Do not create `tests/_support/fakes`, `tests/**/_fakes.py`, generic
  `_scenarios.py`, fake modules outside those mirrored unit port/capability
  packages, or double classes in `conftest.py`.
- Use `MagicMock` or `AsyncMock` inline in the test function when only one
  behavior needs to be changed for that scenario. Prefer autospeccing when
  call signatures matter and `spec_set` when unexpected attributes must fail.
- Unit tests replace external IO, time, randomness, network, Redis, database,
  and framework resources with local doubles or inline mocks.
- Integration tests use the real internal app graph. Do not mock internal use
  cases, services, or capabilities; stub only external systems when needed.
- Add core use-case integration tests under `tests/integration/core/...` for
  use cases that inject a UoW manager; delivery tests should own HTTP mapping,
  not be the only persistence proof.
- Persistence integration tests use the production database family when
  dialect behavior matters. A rollback harness may not replace isolated
  commit-visible tests for locking, concurrency, isolation, or after-commit
  behavior.
- Core health tests cover required-dependency readiness and any reusable probe
  services and use cases.
  Delivery probe tests cover `/healthz` and `/readyz` as operational endpoints,
  not versioned business API routes. `/healthz` must prove a lightweight
  process response only; `/readyz` must prove required infrastructure readiness,
  including a real bounded DB check for SQLAlchemy services.
- Probe route tests assert `Cache-Control: no-store`, readiness failure returns
  `503`, probe routes are excluded from OpenAPI, and legacy `/api/v1/health` is
  absent when replacing old generated health endpoints.
- Unit-test logging configurators by overriding logging settings,
  monkeypatching `logging.config.dictConfig`, and asserting the generated
  stdlib config. Use `caplog` only when a log record is meaningful behavior.
- Unit-test FastAPI lifecycle managers by overriding closeable infrastructure
  resources and asserting shutdown order. Route integration helpers must run
  ASGI lifespan explicitly.
- Use `httpx2`, not legacy `httpx`, for generated HTTP client and ASGI transport
  tests. Enter `LifespanManager`, then pass the yielded manager's `manager.app`
  to `ASGITransport` so request scopes receive lifespan state.
- FastAPI route tests compare response status codes with `fastapi.status`
  constants, not raw integer literals.
- Use `container.resolve(...)` for normal synchronous graph construction, even
  when the resolved use case has an async `execute(...)`; use
  `await container.aresolve(...)` only when DI construction itself has async
  providers.
- Mock fixtures should register one external collaborator for the behavior
  under test. Do not bundle unrelated mocks in a dict or class-keyed fixture.
- Use native pytest fixtures for test dependencies. Do not enable
  `diwire.integrations.pytest_plugin`, and do not use `Injected[...]`
  parameters in tests.
- AnyIO runs tests on every installed supported backend by default. If the app
  graph is asyncio-specific, override the top-level `anyio_backend` fixture to
  return `"asyncio"`; leave it unpinned only when the suite intentionally
  supports every installed backend.
- Do not add filler smoke tests that only assert `container.resolve(...)`
  returns an instance.
- Do not hand-build application graphs in test bodies. Resolve project classes
  from the container; local test doubles may be instantiated in the test module
  before registration.
- Keep unit tests free from FastAPI request objects and real external IO.
- Every test directory must include an empty `__init__.py` file.
- Use the packaged architecture wrapper as the default guardrail mechanism for
  Specx boundaries such as docstrings, use-case inputs, UoW injection, route
  paths, direct persistence dependency rejection in use cases, container
  imports, and `AGENTS.md` command coverage.
- Disable built-in guardrails only with explicit `SpecxRuleId` values and a
  project reason recorded beside the disabled value.
- Add `extra_rules` only for project-specific checks that are not covered by a
  built-in `SpecxRuleId`.
- Existing workflows may use `references/render_architecture_guardrails.py` to
  render the tiny wrapper.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/testing.md` - folder layout, fixtures, unit/integration examples,
  and architecture guardrail snippets.
- `references/render_architecture_guardrails.py` - compatibility renderer for
  the tiny `specx` architecture wrapper.
