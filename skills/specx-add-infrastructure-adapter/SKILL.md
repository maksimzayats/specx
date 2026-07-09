---
name: specx-add-infrastructure-adapter
description: Add technical infrastructure adapters for Specx core scopes. Use when implementing SQLAlchemy repositories and Alembic-backed persistence, Redis stores, HTTP/network clients, file or queue adapters, unit-of-work implementations, gateway implementations for external APIs or SDKs such as OpenAI, or explicit `diwire` bindings for core scope repository and gateway ports.
---

# Specx Add Infrastructure Adapter

Use this skill whenever code talks to external systems. Read
`references/adapter.md` before writing adapters.

## Workflow

1. Define or reuse a repository under `repositories/` for owned persistence.
   Repository ports inherit `BaseRepository` and mark required methods with
   `@abstractmethod`.
2. Define or reuse a gateway under `gateways/` for outbound business
   capabilities to external systems such as OpenAI, payments, email, queues, or
   external HTTP APIs. Gateway ports inherit `BaseGateway`, mark required
   methods with `@abstractmethod`, declare external effects, and do not return
   entities.
3. Put concrete implementations under
   `core/<scope>/infrastructure/<technology>/`.
4. Inject external clients, session factories, Redis clients, SDK clients, or
   project-owned client factories. Do not hide client construction inside
   business methods.
5. Keep technical query/request code in infrastructure.
6. Repositories may return entities. Gateways must not return entities; return
   DTOs, primitives, value objects, or explicit result objects. Do not return
   ORM models or SDK response objects to core.
7. Translate low-level exceptions into core exceptions only when callers need to
   handle them.
8. For transactional persistence, implement an active `UnitOfWork` and a
   `UnitOfWorkManager`; register the manager, not repositories, active UoWs,
   or UoW providers for use-case injection.
9. Register adapter bindings in private `_register_dependencies(...)` inside
   `ioc/container.py`.
10. Add focused integration tests only when the adapter has meaningful
    project-owned behavior to protect; do not add generic CRUD or upstream
    library tests just because an adapter file exists.
11. For SQLAlchemy adapters, add or update Alembic migrations with
   `$specx-sqlalchemy-migrations`.

Logging is top-level runtime infrastructure, not a core-scope adapter. Put
stdlib logging setup in `infrastructure/logging/LoggingConfigurator`, inherit
`BaseConfigurator`, and do not create gateway ports or injected logger
bindings for it.

For `/readyz`, implement required dependency checks as `core/health` gateway
adapters, for example
`core/health/infrastructure/sqlalchemy/readiness_check_gateway.py`, and bind
them to `ReadinessCheckGateway` in `ioc/container.py`.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/adapter.md` - adapter layout, port binding, SQLAlchemy/UoW, Redis,
  HTTP client, migration, and test patterns.
