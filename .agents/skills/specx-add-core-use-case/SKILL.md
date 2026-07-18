---
name: specx-add-core-use-case
description: Add or refactor a specx core scope use case. Use when implementing an externally meaningful application action under a core scope use_cases package, adding same-file command/query inputs, result DTOs, coordinating services, opening a unit-of-work transaction, or moving behavior out of delivery or infrastructure into class-based application code.
---

# specx Add Core Use Case

Use this skill for one application action at a time. Read
`references/use-case.md` before writing the use case.

## Workflow

1. Name the action directly, for example `CreateInvoiceUseCase`.
2. Put it under `core/<scope>/use_cases/<action>.py`.
3. Inherit `BaseUseCase` from `specx.core.foundation.use_case`.
4. Define exactly one same-file input class: a `Command` for state-changing
   use cases or a `Query` for read-only use cases. Even empty inputs are
   explicit.
5. Make commands inherit `specx.core.foundation.command.BaseCommand`, queries inherit
   `specx.core.foundation.query.BaseQuery`, and result DTOs inherit
   `specx.core.foundation.dto.BaseDTO`. Prefer
   `@dataclass(frozen=True, kw_only=True, slots=True)` for all of these core
   data classes unless the user asks for another model type.
6. Treat commands and queries as input contracts, not DTOs. Do not make
   commands or queries inherit `BaseDTO`, put them under `dtos/`, or add a
   `DTO` suffix.
7. `execute(...)` accepts exactly one keyword-only argument named `command` or
   `query` and returns DTOs, not entities.
8. Inject services, capabilities, gateways, and UoW managers with
   `Injected[...]`. Keep infrastructure/runtime settings out of core use cases;
   expose required business policy as a typed core value or collaborator. For
   transactional persistence, inject the scope
   `UnitOfWorkManager` and open the active unit of work inside `execute(...)`.
   Do not inject repositories, SQLAlchemy sessions/engines/session factories,
   or concrete infrastructure adapters directly into use cases.
9. Keep framework schemas, routers, ORM models, Redis clients, HTTP clients,
   and entity return types
   out of the use case.
10. Mark secret-bearing dataclass fields with `field(repr=False)` and never log
    whole commands, queries, or DTOs that may contain sensitive values.
11. Add or update flat unit tests for the behavior. The test receives the
    native pytest `container` fixture, registers local doubles or inline mocks
    before resolution, and resolves the use case with
    `container.resolve(UseCaseClass)`. If the use case injects a
    `UnitOfWorkManager`, also add a core integration test under
    `tests/integration/core/...` against the real persistence graph (and the
    transactional database graph when database-backed).

`CheckReadinessUseCase` may live under `core/health` when readiness checks any
required external dependency or multiple delivery layers reuse the policy. Add
a core `CheckLivenessUseCase` only when framework-independent liveness policy
is genuinely reused across deliveries; keep a simple process-only liveness
response in delivery. HTTP paths, status codes, headers, and schemas always
stay in delivery.

## Transaction Rule

A use case may open one unit-of-work scope inside `execute(...)` when database
work is part of the action. Inject the manager, not `Provider[UnitOfWork]` and
not an active UoW instance, repository, SQLAlchemy session/engine/session
factory, or concrete infrastructure adapter. Read/effect services may receive
the active `unit_of_work`, but services do not open transactions. Repository
calls from a use case stay rooted in the manager-owned `unit_of_work` variable.

Commands are allowed to change state. Queries are read-only and should not call
repository mutators such as `add`, `save`, `create`, `update`, or `delete`, or
invoke gateways with external write effects.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/use-case.md` - use-case class shape, DTO examples, UoW examples,
  and test guidance.
