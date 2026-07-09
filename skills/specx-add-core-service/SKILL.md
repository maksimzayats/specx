---
name: specx-add-core-service
description: Add or refactor a Specx core scope service. Use when implementing focused reusable business/application behavior under a core scope services package, extracting logic from a use case, injecting deterministic collaborators, accepting an active unit of work, choosing between Service and Capability, or keeping business decisions away from delivery and infrastructure.
---

# Specx Add Core Service

Use this skill for reusable core behavior that is smaller than an application
action. Read `references/service.md` before writing the service.

## Workflow

1. Confirm this is reusable business/application behavior, not a small
   replaceable ability. Use `BaseCapability` instead for one narrow injectable
   thing.
2. Name the behavior, not a vague role, and always use the `Service` suffix:
   `PasswordHashingService`, `InvoicePricingService`, `AccessPolicyService`,
   `TokenIssuingService`.
3. Put it under `core/<scope>/services/<behavior>.py`.
4. Choose exactly one foundation base:
   `BasePureService`, `BaseReadService`, or `BaseEffectService`.
5. Do not add or use a generic `BaseService`.
6. Inject concrete project collaborators when there is one implementation.
7. Inject ports/ABCs only for external IO, framework-bound dependencies, or
   multiple real implementations.
8. Add a docstring that explains the service scope and includes a concrete
   `Example:`.
9. Keep methods keyword-only after `self`.
10. Do not open UoW scopes in services. Use cases own transaction lifecycle and
   pass active UoWs into read/effect services when needed.
11. Add flat unit tests that receive the native pytest `container` fixture,
    register local doubles or inline mocks before resolution, and resolve the
    service with `container.resolve(ServiceClass)`.

Reusable operational probe services may live under `core/health`. Use a pure
service for liveness and a read service for readiness coordination. Readiness
services depend on gateway ports, not SQLAlchemy, Redis, SDKs, or delivery
frameworks directly.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/service.md` - class shape, dependency choices, UoW parameter
  rules, and unit-test examples.
