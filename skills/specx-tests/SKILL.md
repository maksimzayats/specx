---
name: specx-tests
description: Add or refine tests for Specx Python services. Use when creating unit tests for use cases/services, integration tests for FastAPI controllers or infrastructure adapters, e2e smoke tests, architecture import guardrails, DI override tests, pytest fixtures, or coverage and boundary checks.
---

# Specx Tests

Use this skill when behavior, wiring, or architecture boundaries need tests.
Read `references/testing.md` before creating test files.

## Test Layers

- `tests/_support/`: private test helpers, bases, clients, DB helpers, and
  fakes. This is not a test suite.
- `tests/unit/`: use cases and services resolved from fresh explicit `diwire`
  test containers with typed fake overrides.
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
- Before adding a test, sanity-check that it would fail for a plausible bug and
  that its assertion protects behavior, a boundary, or a contract.
- Add tests only when they make sense. Do not add nonsense tests just to have a
  mirrored file, and do not prove upstream libraries such as SQLAlchemy,
  Alembic, HTTPX, or FastAPI work.
- Unit tests replace external IO, time, randomness, network, Redis, database,
  and framework resources with fakes or fixtures.
- Integration tests use the real internal app graph. Do not mock internal use
  cases or services; stub only external systems when needed.
- Add core use-case integration tests under `tests/integration/core/...` when
  persistence behavior matters; delivery tests should own HTTP mapping, not be
  the only persistence proof.
- FastAPI route tests compare response status codes with `fastapi.status`
  constants, not raw integer literals.
- Override DI dependencies before resolving the target graph.
- Mock fixtures should register one external collaborator for the behavior
  under test. Do not bundle unrelated mocks in a dict or class-keyed fixture.
- Use native pytest fixtures for test dependencies. Do not enable
  `diwire.integrations.pytest_plugin`, and do not use `Injected[...]`
  parameters in tests.
- Do not add filler smoke tests that only assert `container.resolve(...)`
  returns an instance.
- Do not hand-build application graphs in test bodies or support factories.
- Keep unit tests free from FastAPI request objects and real external IO.
- Every test directory must include an empty `__init__.py` file.
- Use the packaged architecture wrapper as the default guardrail mechanism for
  Specx boundaries such as docstrings, use-case inputs, UoW injection, route
  paths, container imports, and `AGENTS.md` command coverage.
- Disable built-in guardrails only with explicit `SpecxRuleId` values and a
  project reason.
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
