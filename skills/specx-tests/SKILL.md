---
name: specx-tests
description: Add or refine tests for Specx Python services. Use when creating unit tests for use cases/services, integration tests for FastAPI controllers or infrastructure adapters, e2e smoke tests, architecture import guardrails, DI override tests, pytest fixtures, or coverage and boundary checks.
---

# Specx Tests

Use this skill when behavior, wiring, or architecture boundaries need tests.
Read `references/testing.md` before creating test files.

## Test Layers

- `tests/unit/`: use cases and services with direct construction and fakes.
- `tests/integration/`: delivery controllers, app factory, container wiring,
  database repositories, Redis adapters, network clients with stubs.
- `tests/e2e/`: optional whole-app smoke flows.
- `tests/architecture/`: the packaged
  `specx.testing.architecture.assert_specx_architecture` wrapper plus any
  genuinely project-specific extra rules.

## Rules

- Test behavior and boundaries, not implementation ceremony.
- Replace external IO, time, randomness, network, Redis, database, and framework
  resources with fakes or fixtures.
- Override DI dependencies before resolving the target graph.
- Keep unit tests free from FastAPI request objects and real external IO.
- Use the packaged architecture wrapper as the default guardrail mechanism for
  Specx boundaries such as docstrings, use-case inputs, UoW injection, route
  paths, container imports, and `AGENTS.md` command coverage.
- Disable built-in guardrails only with explicit `SpecxRuleId` values and a
  project reason.
- Add `extra_rules` only for project-specific checks that are not covered by a
  built-in `SpecxRuleId`.
- Existing workflows may use `references/render_architecture_guardrails.py` to
  render the tiny wrapper.

## References

- `references/testing.md` - folder layout, fixtures, unit/integration examples,
  and architecture guardrail snippets.
- `references/render_architecture_guardrails.py` - compatibility renderer for
  the tiny `specx` architecture wrapper.
