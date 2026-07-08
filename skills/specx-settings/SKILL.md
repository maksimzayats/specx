---
name: specx-settings
description: Add runtime configuration to Specx Python services with `pydantic-settings`. Use when creating settings classes, environment variables, `.env.example`, injecting settings into services or adapters, documenting config, or removing direct environment reads from core code.
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
- Inject settings objects. Do not read `os.environ` inside use cases or
  services.
- Use clear environment variable names and safe defaults only when safe.
- Keep secrets out of examples.
- Update `.env.example` when adding user-provided environment variables.
- Override environment values in tests with fixtures or `monkeypatch`.
- Do not inherit raw `BaseSettings` outside `foundation/settings.py`.

## References

- `references/settings.md` - settings placement, examples, env naming, and test
  overrides.
