---
name: specx-add-core-use-case
description: Add or refactor a Specx core scope use case. Use when implementing an externally meaningful application action under a core scope use_cases package, adding same-file command/query inputs, result DTOs, coordinating services, opening a unit-of-work transaction, or moving behavior out of delivery or infrastructure into class-based application code.
---

# Specx Add Core Use Case

Use this skill for one application action at a time. Read
`references/use-case.md` before writing the use case.

## Workflow

1. Name the action directly, for example `CreateInvoiceUseCase`.
2. Put it under `core/<scope>/use_cases/<action>.py`.
3. Inherit `BaseUseCase` from `specx.foundation.use_case`.
4. Define exactly one same-file input class: a `Command` for state-changing
   use cases or a `Query` for read-only use cases. Even empty inputs are
   explicit.
5. Make commands inherit `specx.foundation.command.BaseCommand`, queries inherit
   `specx.foundation.query.BaseQuery`, and result DTOs inherit
   `specx.foundation.dto.BaseDTO`. Prefer
   `@dataclass(frozen=True, kw_only=True, slots=True)` for all of these core
   data classes unless the user asks for another model type.
6. `execute(...)` accepts exactly one keyword-only argument named `command` or
   `query` and returns DTOs, not entities.
7. Inject services, capabilities, repositories, gateways, and settings with
   `Injected[...]`. For transactional persistence, inject the scope
   `UnitOfWorkManager` and open the active unit of work inside `execute(...)`.
8. Keep framework schemas, routers, ORM models, Redis clients, HTTP clients,
   and entity return types
   out of the use case.
9. Add or update unit tests for the behavior.

## Transaction Rule

A use case may open one unit-of-work scope inside `execute(...)` when database
work is part of the action. Inject the manager, not `Provider[UnitOfWork]` and
not an active UoW instance. Read/effect services may receive the active
`unit_of_work`, but services do not open transactions.

Commands are allowed to change state. Queries are read-only and should not call
repository mutators such as `add`, `save`, `create`, `update`, or `delete`.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/use-case.md` - use-case class shape, DTO examples, UoW examples,
  and test guidance.
