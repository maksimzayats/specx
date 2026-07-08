# Specx Testing Reference

Tests should prove behavior and protect boundaries without recreating the
application inside test helpers.

## Layout

```text
tests/
  unit/
  integration/
  e2e/
  architecture/
```

Create only folders that contain real tests. Use `unit/` for isolated core
behavior, `integration/` for delivery/container/persistence paths, `e2e/` for
optional whole-app smoke flows, and `architecture/` for the `specx` guardrail
wrapper.

## Unit Tests

Construct simple use cases and services directly. Use real deterministic
collaborators and fake only external IO, time, randomness, network clients,
database sessions, and framework resources.

```python
def test_check_health_returns_ok() -> None:
    use_case = CheckHealthUseCase(
        _health_reporter_service=HealthReporterService(),
    )

    result = use_case.execute(query=CheckHealthQuery())

    assert result.status == "ok"
```

For async code, use the repo's chosen async pytest plugin consistently.

## Integration Tests

Resolve production graphs from the container only after applying any test
overrides. Keep each integration test focused on one boundary: route to use
case, container to graph, repository to database, or migration to metadata.

```python
from fastapi.testclient import TestClient


def test_health_route(container: Container) -> None:
    app = container.resolve(FastAPIFactory)()

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Container fixture:

```python
import pytest
from diwire import Container

from order_service.ioc.container import get_container


@pytest.fixture()
def container() -> Container:
    return get_container()
```

## Architecture Guardrails

For full Specx service guardrails, add the tiny pytest wrapper around the
`specx` package:

```python
from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    assert_specx_architecture,
)


def test_specx_architecture() -> None:
    disabled_rules: frozenset[SpecxRuleId] = frozenset()

    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[2],
            package_name="order_service",
            disabled_rules=disabled_rules,
        )
    )
```

Disable project-specific exceptions explicitly with stable rule IDs:

```python
disabled_rules = frozenset({
    SpecxRuleId.CLASSES_REQUIRE_EXAMPLE_DOCSTRINGS,
})
```

Existing workflows can render the wrapper:

```bash
cd /path/to/installed/specx-tests
uv run python references/render_architecture_guardrails.py \
  --package order_service \
  --output /path/to/project/tests/architecture/test_boundaries.py
```

Do not vendor a local copy of the rule engine into generated projects. Treat
the packaged wrapper as the default architecture-test mechanism. Add
`extra_rules` only for project-specific guardrails that are not covered by a
built-in `SpecxRuleId`, then keep the custom rule in the project's tests and
pass it through `SpecxArchitectureConfig(extra_rules=...)`.

```python
from specx.testing.architecture import (
    ArchitectureContext,
    BaseRule,
    SpecxArchitectureViolation,
)


class NoLegacyImportsRule(
    BaseRule[str, ArchitectureContext, SpecxArchitectureViolation],
):
    """Reject legacy module imports while the project completes migration."""

    id = "project.no-legacy-imports"

    def check(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        return ()
```

## DI Tests

- Override dependencies before resolving the target object graph.
- Reset or rebuild containers per test when overrides are mutable.
- Prefer direct construction for simple services when it is clearer than the
  container.
- Keep tests from reaching into private container registration details unless
  the test is specifically about wiring.

## Persistence And Migrations

- SQLAlchemy projects use Alembic in tests and production paths.
- Do not call `metadata.create_all()` or `drop_all()` in source or tests.
- Use temporary database URLs for migration and repository tests.
- Run `alembic upgrade head` before repository integration assertions.
- Include a migration drift check when the project owns SQLAlchemy models.

## Avoid

- No framework request objects in unit tests for use cases or core services.
- No global settings singleton hidden in core tests.
- No broad fixtures that hide the behavior under test.
- No duplicated architecture rule modules in generated projects.
- No tests for empty folders or speculative future structure.
