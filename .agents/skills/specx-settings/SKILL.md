---
name: specx-settings
description: Add runtime configuration to Specx Python services with `pydantic-settings`. Use when creating settings classes, environment variables, `.env.example`, injecting settings at delivery, infrastructure, or composition edges, documenting config, mapping configuration into typed core policy collaborators, or removing direct environment reads from core code.
---

# Specx Settings

Use this skill whenever runtime configuration is needed. Read
`references/settings.md` before adding settings code.

## Rules

- Model runtime config with classes that inherit `BaseRuntimeSettings`.
- Give each settings class a docstring that explains the configuration scope
  and includes a concrete `Example:`.
- Place settings near the class that consumes them unless the setting is truly
  application-wide.
- Logging settings are application-wide and live beside
  `infrastructure/logging/configurator.py` and its `LoggingConfigurator`.
- Use `BaseStrEnum` for finite configuration values such as logging levels.
- Inject settings objects only into delivery, infrastructure, and composition
  classes. Do not inject `BaseRuntimeSettings` subclasses into core use cases,
  services, capabilities, entities, repositories, or gateway ports.
- When configuration represents a genuine business policy, map it at the
  composition root into a typed core value or capability that has no dependency
  on Pydantic or `BaseRuntimeSettings`.
- Let `diwire` auto-register settings as root-scoped singletons. Register a
  settings instance explicitly only for an intentional override.
- At operational entrypoints, load required runtime values with
  `SettingsClass.from_environment()`. Build explicit test or composition
  overrides with `SettingsClass.model_validate({...})` so strict type checking
  does not mistake raw input strings for already-validated field types.
- Do not read `os.environ` outside settings classes or composition code.
- Use clear environment variable names and safe defaults only when safe.
- Type secret fields with `SecretStr`, keep secrets out of examples, and unwrap
  them only at the adapter call that needs the raw value.
- Update `.env.example` when adding user-provided environment variables.
- Isolate settings-source tests from a developer's `.env` by changing to
  `tmp_path`, then override environment values with `monkeypatch`.
- Do not inherit raw `BaseSettings`; inherit
  `specx.infrastructure.foundation.settings.BaseRuntimeSettings`.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/settings.md` - settings placement, examples, env naming, and test
  overrides.
