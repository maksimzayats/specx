---
name: specx-add-core-service
description: Add or refactor a Specx core scope service. Use when implementing focused reusable behavior under a core scope services package, extracting logic from a use case, injecting deterministic collaborators, accepting an active unit of work, or keeping business decisions away from delivery and infrastructure.
---

# Specx Add Core Service

Use this skill for reusable core behavior that is smaller than an application
action. Read `references/service.md` before writing the service.

## Workflow

1. Name the behavior, not a vague role, and always use the `Service` suffix:
   `PasswordHashingService`, `InvoicePricingService`, `AccessPolicyService`,
   `TokenIssuingService`.
2. Put it under `core/<scope>/services/<behavior>.py`.
3. Inherit `BaseService` from `foundation/service.py`.
4. Inject concrete project collaborators when there is one implementation.
5. Inject ports/ABCs only for external IO, framework-bound dependencies, or
   multiple real implementations.
6. Add a docstring that explains the service scope and includes a concrete
   `Example:`.
7. Keep methods keyword-only after `self`.
8. Do not open UoW scopes in services.
9. Add direct unit tests with deterministic fakes where needed.

## References

- `references/service.md` - class shape, dependency choices, UoW parameter
  rules, and unit-test examples.
