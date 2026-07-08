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
- `tests/architecture/`: import direction, route path, container, UoW, and
  framework-boundary guardrails.

## Rules

- Test behavior and boundaries, not implementation ceremony.
- Replace external IO, time, randomness, network, Redis, database, and framework
  resources with fakes or fixtures.
- Override DI dependencies before resolving the target graph.
- Keep unit tests free from FastAPI request objects and real external IO.
- Add architecture tests for major class docstrings with concrete `Example:`
  blocks.
- Add architecture tests that every use case accepts one same-file `Command` or
  `Query` input and that queries avoid obvious repository mutators.
- Add architecture tests that persistence use cases inject
  `Injected[*UnitOfWorkManager]`, not `Provider[UnitOfWork]` or an active
  `*UnitOfWork`.
- Add architecture tests only for rules that are likely to regress.

## References

- `references/testing.md` - folder layout, fixtures, unit/integration examples,
  and architecture guardrail snippets.
