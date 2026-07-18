---
name: specx-add-infrastructure-adapter
description: Add technical infrastructure adapters for specx core scopes. Use when implementing SQLAlchemy repositories and Alembic-backed persistence, Redis stores, HTTP/network clients, file or queue adapters, unit-of-work implementations, gateway implementations for external APIs or SDKs such as OpenAI, or explicit `diwire` bindings for core scope repository and gateway ports.
---

# specx Add Infrastructure Adapter

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
   business methods. Generated HTTP adapters use `httpx2`, imported from the
   `httpx2` namespace; do not generate new legacy `httpx` imports.
5. A bounded short-lived client factory may stay beside its scope adapter. Put
   every app-owned pooled client factory or wrapper under top-level
   `infrastructure/<technology>/`, even with only one current consumer.
6. Give long-lived app-owned infrastructure resources an explicit async
   `close()` method; FastAPI lifecycle owns calling it on shutdown.
7. Keep technical query/request code in infrastructure.
8. Repositories may return entities. Gateways must not return entities; return
   DTOs, primitives, enums, or explicit result objects. Do not return ORM
   models or SDK response objects to core.
9. Translate low-level exceptions into core exceptions only when callers need to
   handle them. Catch narrow driver or SDK exceptions, preserve the cause, and
   never expose raw provider messages, SQL, parameters, bodies, or URLs.
10. For transactional persistence, implement an active `UnitOfWork` and a
   `UnitOfWorkManager`; register the manager, not repositories, active UoWs,
   or UoW providers for use-case injection.
11. Register adapter bindings in private `_register_dependencies(...)` inside
   `ioc/container.py`. Register every technical resource once at its owner
   boundary and close that same app-scoped instance from lifecycle.
12. Add focused integration tests only when the adapter has meaningful
   project-owned behavior to protect; do not add generic CRUD or upstream
   library tests just because an adapter file exists.
13. For SQLAlchemy adapters, add or update Alembic migrations with
   `$specx-sqlalchemy-migrations`.

Logging is top-level runtime infrastructure, not a core-scope adapter. Put
stdlib logging setup in `infrastructure/logging/configurator.py` with a
`LoggingConfigurator` that inherits `BaseConfigurator`; do not create gateway
ports or injected logger bindings for it.

For `/readyz`, implement required dependency checks as `core/health` gateway
adapters, for example
`core/health/infrastructure/sqlalchemy/readiness_check_gateway.py`, and bind
them to `ReadinessCheckGateway` in `ioc/container.py`. Bound every dependency
check with a short application timeout and return only a non-sensitive core
status.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/adapter.md` - adapter layout, port binding, SQLAlchemy/UoW, Redis,
  HTTP client, migration, and test patterns.
