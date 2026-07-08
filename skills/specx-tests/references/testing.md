# Specx Testing Reference

Tests should prove behavior and protect boundaries while letting `diwire`
assemble application graphs explicitly through native pytest fixtures. Test
bodies should receive resolved components, scenario fakes, or container-backed
test clients from fixtures.

## Layout

Mirror source paths under the test layer that owns the behavior:

```text
tests/
  _support/
    bases/
    clients/
    db/
    fakes/
      core/
  guardrails/
    architecture/
      test_boundaries.py
  unit/
    core/
      <scope>/
        services/test_<service_module>.py
        use_cases/test_<use_case_module>.py
        capabilities/test_<capability_module>.py
  integration/
    core/
      <scope>/
        use_cases/test_<use_case_module>.py
    delivery/<framework>/
    migrations/test_alembic.py
```

Create only folders that contain real tests. If a test targets a source module,
its path should mirror that module below `tests/unit` or `tests/integration`.
Private support code lives under `tests/_support` and must not be treated as a
test suite. Architecture policy checks live under `tests/guardrails`, because
they enforce project rules rather than test one application layer. Migration
tests remain the non-mirrored integration exception.

Every directory under `tests/` must include an empty `__init__.py` file. Do not
add re-exports, imports, or setup behavior there.

The required mirrored scope is currently only core services, use cases, and
capabilities. Do not create repository, UoW, model, session, or adapter tests
only to mirror source files.

## Unit Tests

Unit tests use a fresh test container, override IO ports with typed fakes, then
resolve the component under test. Do not manually instantiate use cases,
services, repositories, UoW managers, or controllers in test bodies. Do not use
`diwire.integrations.pytest_plugin` or `Injected[...]` test parameters.

```python
@pytest.fixture
def container() -> Container:
    container = get_container()
    repository = InMemoryTaskRepository()
    unit_of_work_manager = InMemoryTaskUnitOfWorkManager(repository=repository)
    container.add_instance(repository, provides=InMemoryTaskRepository)
    container.add_instance(unit_of_work_manager, provides=TaskUnitOfWorkManager)
    return container


@pytest.fixture
def create_task_use_case(container: Container) -> CreateTaskUseCase:
    return container.resolve(CreateTaskUseCase)


@pytest.mark.anyio
async def test_create_task_normalizes_title(
    create_task_use_case: CreateTaskUseCase,
) -> None:
    result = await create_task_use_case.execute(
        command=CreateTaskCommand(title="  Ship skill  "),
    )

    assert result.title == "Ship skill"
```

Use typed fakes for boundaries such as repositories, UoW managers, clocks,
generators, network clients, queues, and SDKs. Keep fakes under
`tests/_support/fakes/...`.

Parameterize aggressively. When a case has more than one meaningful field, use
a small dataclass and inline the case list directly in `pytest.mark.parametrize`
unless the same case set is reused by multiple tests.

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class NormalizeTitleCase:
    id: str
    raw_title: str
    expected_title: str


@pytest.mark.parametrize(
    "case",
    [
        NormalizeTitleCase(
            id="trims_edges",
            raw_title="  Ship skill  ",
            expected_title="Ship skill",
        ),
        NormalizeTitleCase(
            id="collapses_inner_space",
            raw_title="Ship   skill",
            expected_title="Ship skill",
        ),
    ],
    ids=lambda case: case.id,
)
def test_normalize_accepts_valid_titles(
    case: NormalizeTitleCase,
    task_title_normalizer_service: TaskTitleNormalizerService,
) -> None:
    assert task_title_normalizer_service.normalize(title=case.raw_title) == case.expected_title
```

## Integration Tests

Integration tests use the real internal application graph: delivery, DI, use
cases, services, UoWs, repositories, and the database. Stub only external
systems. Apply overrides before resolving the target graph. Resolve the factory
first, then call it.

```python
class TestAsyncClientFactory(ContainerBasedFactory):
    async def __call__(self) -> AsyncIterator[AsyncClient]:
        app_factory = self._container.resolve(FastAPIFactory)
        app = app_factory()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
```

Core use-case integration tests call resolved use cases directly against the
transactional DB. They own persistence-facing application contracts:

```python
@pytest.mark.anyio
async def test_execute_normalizes_and_persists_task(
    create_task_use_case: CreateTaskUseCase,
    list_tasks_use_case: ListTasksUseCase,
) -> None:
    created_task = await create_task_use_case.execute(
        command=CreateTaskCommand(title="  Ship skill  "),
    )
    listed_tasks = await list_tasks_use_case.execute(query=ListTasksQuery())

    assert created_task.title == "Ship skill"
    assert listed_tasks.tasks == [created_task]
```

FastAPI route tests use the transactional client backed by the real database:

```python
from fastapi import status


@pytest.mark.anyio
async def test_create_task_route_persists_normalized_title(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.post("/api/v1/tasks", json={"title": "  Ship skill  "})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "Ship skill"
```

Do not mock internal use cases or services in integration tests. Only add
repository, UoW, model, session, or adapter integration tests when they cover
meaningful project-owned behavior: nontrivial mapping, query shape, exception
translation, lifecycle policy, or a regression that would not be covered
through a use case or route. Do not add generic CRUD round-trip tests or tests
that prove SQLAlchemy/session/upstream behavior.

Only add direct container tests when they prove a meaningful explicit binding
or lifecycle rule. Do not add tests that only assert `container.resolve(...)`
returns an instance.

## Database Isolation

For SQLAlchemy projects:

- Run Alembic once for a session-scoped migrated SQLite database.
- For each data integration test, open one connection and an outer
  transaction.
- Bind sessions with `join_transaction_mode="create_savepoint"`.
- Roll back the outer transaction in teardown.
- For SQLite/aiosqlite, create the test engine with
  `connect_args={"autocommit": False}` so SAVEPOINT work stays inside the
  outer transaction.
- Migration tests still use fresh temp database files because DDL is the
  behavior under test.

Do not call `metadata.create_all()` or `drop_all()` in source or tests.

## Architecture Guardrails

Use the packaged architecture wrapper:

```python
from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    assert_specx_architecture,
)


def test_specx_architecture() -> None:
    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[3],
            package_name="order_service",
            disabled_rules=frozenset(),
        )
    )
```

`SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE` is enabled by default. Disable it
only for deliberate legacy migrations.

## Avoid

- No hand-built application graphs in tests or support factories.
- No public helper folders next to test suites. Put helper code under
  `tests/_support`.
- No filler tests. Before adding a test, check that it would fail for a
  plausible bug and that the assertion protects behavior, a boundary, or a
  contract.
- No repository/UoW/model/session tests just to mirror source files.
- No tests whose real assertion is that an upstream library works.
- No tests that only assert `container.resolve(...)` returns an instance.
- No internal use-case or service mocks in integration tests.
- No raw integer status codes in FastAPI route assertions; use
  `fastapi.status` constants.
- No grouped mock fixtures that register several unrelated collaborators for a
  test that exercises only one of them.
- No `container.resolve(FastAPIFactory)()` inline; resolve the factory first,
  then call it.
- No framework request objects in unit tests.
- No SQLAlchemy sessions, FastAPI apps, or real IO in unit tests.
- No broad autouse fixtures that hide DB, settings, or container state.
- No global shared containers across tests.
- No placeholder tests for empty folders or future structure.
- No missing test package initializers; every test directory has an empty
  `__init__.py`.
