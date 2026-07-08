---
name: specx-add-infrastructure-adapter
description: Add technical infrastructure adapters for Specx core scopes. Use when implementing SQLAlchemy repositories and Alembic-backed persistence, Redis stores, HTTP/network clients, file or queue adapters, unit-of-work implementations, external SDK wrappers, or explicit `diwire` bindings for core scope repository ports.
---

# Specx Add Infrastructure Adapter

Use this skill whenever code talks to external systems. Read
`references/adapter.md` before writing adapters.

## Workflow

1. Define or reuse a repository/port under `repositories/` only when the
   dependency is external IO, framework-bound, or selected by configuration.
   Repository ports inherit `BaseRepository`.
2. Put concrete implementations under
   `core/<scope>/infrastructure/<technology>/`.
3. Inject external clients, session factories, Redis clients, SDK clients, or
   project-owned client factories. Do not hide client construction inside
   business methods.
4. Keep technical query/request code in infrastructure.
5. Return core DTOs/entities or primitive result values. Do not return ORM
   models or SDK response objects to core.
6. Translate low-level exceptions into core exceptions only when callers need to
   handle them.
7. For transactional persistence, implement an active `UnitOfWork` and a
   `UnitOfWorkManager`; register the manager, not a UoW provider.
8. Register adapter bindings in private `_register_dependencies(...)` inside
   `ioc/container.py`.
9. Add focused integration tests for adapter behavior.
10. For SQLAlchemy adapters, add or update Alembic migrations with
   `$specx-sqlalchemy-migrations`.

## References

- `references/adapter.md` - adapter layout, port binding, SQLAlchemy/UoW, Redis,
  HTTP client, migration, and test patterns.
