# Specx Testing Reference

Tests should prove behavior and protect boundaries.

## Layout

```text
tests/
  unit/
    core/
  integration/
    core/
    delivery/
    ioc/
  e2e/
  architecture/
```

Create only folders that contain real tests.

## Unit Tests

Use direct construction for core classes:

```python
def test_check_health_returns_ok() -> None:
    use_case = CheckHealthUseCase(
        _health_reporter_service=HealthReporterService(),
    )

    result = use_case.execute(query=CheckHealthQuery())

    assert result.status == "ok"
```

For async code, use `pytest.mark.anyio` or `pytest.mark.asyncio` depending on
the repo's chosen plugin.

## Integration Tests

Resolve from the container only after overrides:

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

Use AST checks for rules that are easy to regress:

The example below is a starter subset for small projects. For a full Specx
service, render the canonical guardrail module bundled with this skill:

```bash
cd /path/to/installed/specx-tests
uv run python references/render_architecture_guardrails.py \
  --package order_service \
  --output /path/to/project/tests/architecture/test_boundaries.py
```

If running the renderer is not practical, copy
`references/architecture_guardrails.py` and replace every
`__SPECX_PACKAGE_NAME__` placeholder with the real import package. The canonical
module contains stricter checks for most-specific foundation base ancestry,
same-file command/query inputs, result DTO placement, direct entity imports,
direct repository result returns, active-UoW and injected repository mutators,
`Injected[*UnitOfWorkManager]`, capability placement and suffixes, gateway
placement and effect declarations, pure/read/effect service categories,
documented `AGENTS.md` command drift, and repeated UoW manager scopes.

```python
import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src" / "order_service"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imports(path: Path) -> set[str]:
    tree = _tree(path)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module_name = "." * node.level + (node.module or "")
            if module_name:
                modules.add(module_name)
            separator = "" if module_name == "" or module_name.endswith(".") else "."
            modules.update(
                f"{module_name}{separator}{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return modules


def _module_parts(module: str) -> tuple[str, ...]:
    return tuple(part for part in module.split(".") if part)


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".")[0]
                aliases[local_name] = alias.name.split(".")[-1]
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local_name = alias.asname or alias.name
                aliases[local_name] = alias.name
    return aliases


def _base_name(base: ast.expr, aliases: dict[str, str] | None = None) -> str:
    aliases = aliases or {}
    if isinstance(base, ast.Name):
        return aliases.get(base.id, base.id)
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Subscript):
        return _base_name(base.value, aliases)
    return ast.unparse(base)


def _annotation_name(annotation: ast.expr | None, aliases: dict[str, str] | None = None) -> str:
    aliases = aliases or {}
    if annotation is None:
        return ""
    if isinstance(annotation, ast.Name):
        return aliases.get(annotation.id, annotation.id)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    if isinstance(annotation, ast.Subscript):
        return (
            f"{_annotation_name(annotation.value, aliases)}"
            f"[{_annotation_name(annotation.slice, aliases)}]"
        )
    if isinstance(annotation, ast.Tuple):
        return ", ".join(_annotation_name(element, aliases) for element in annotation.elts)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return (
            f"{_annotation_name(annotation.left, aliases)} | "
            f"{_annotation_name(annotation.right, aliases)}"
        )
    return ast.unparse(annotation)


def _source_paths() -> list[Path]:
    return [
        path
        for path in SRC_ROOT.rglob("*.py")
        if path.name != "__init__.py"
    ]


INNER_PACKAGE_NAMES = {
    "capabilities",
    "dtos",
    "entities",
    "exceptions",
    "gateways",
    "repositories",
    "services",
    "use_cases",
}
BASE_SUFFIXES = (
    "ApplicationValueError",
    "ApplicationError",
    "DeliveryService",
    "FastAPISchema",
    "RuntimeSettings",
    "SQLAlchemyModel",
    "Configurator",
    "UnitOfWorkManager",
    "Capability",
    "Command",
    "Controller",
    "Gateway",
    "Repository",
    "UnitOfWork",
    "UseCase",
    "Entity",
    "Factory",
    "Model",
    "Schema",
    "Service",
    "Settings",
    "ValueError",
    "Error",
    "Enum",
    "DTO",
    "Query",
)
BASE_SUFFIX_OVERRIDES = {
    "ApplicationError": "Error",
    "ApplicationValueError": "ValueError",
    "DeliveryService": "Service",
    "FastAPISchema": "Schema",
    "RuntimeSettings": "Settings",
    "SQLAlchemyModel": "Model",
    "StrEnum": "Enum",
}


def _class_suffix_from_base(base_name: str) -> str | None:
    normalized_base_name = base_name.removeprefix("Base")
    if normalized_base_name in BASE_SUFFIX_OVERRIDES:
        return BASE_SUFFIX_OVERRIDES[normalized_base_name]

    return next(
        (
            suffix
            for suffix in BASE_SUFFIXES
            if normalized_base_name.endswith(suffix)
        ),
        None,
    )


def _has_scoped_example_docstring(node: ast.ClassDef) -> bool:
    docstring = ast.get_docstring(node)
    if docstring is None or "Example:" not in docstring:
        return False
    scope, _separator, example = docstring.partition("Example:")
    if any(line.strip() in {"...", "pass"} for line in example.splitlines()):
        return False
    example_lines = [
        line.strip()
        for line in example.splitlines()
        if line.strip()
    ]
    return scope.strip() != "" and example_lines != []


def _class_direct_base_names(
    node: ast.ClassDef,
    aliases: dict[str, str],
) -> set[str]:
    return {_base_name(base, aliases) for base in node.bases}


def _class_base_name_index() -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for path in _source_paths():
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                index[node.name] = _class_direct_base_names(node, aliases)
    return index


def _foundation_base_names_for_class(
    class_name: str,
    class_base_name_index: dict[str, set[str]],
    *,
    visited: set[str] | None = None,
) -> set[str]:
    visited = visited or set()
    if class_name in visited:
        return set()
    visited.add(class_name)

    base_names = class_base_name_index.get(class_name, set())
    foundation_base_names = {
        base_name for base_name in base_names if _class_suffix_from_base(base_name) is not None
    }
    for base_name in base_names:
        foundation_base_names.update(
            _foundation_base_names_for_class(
                base_name,
                class_base_name_index,
                visited=visited,
            ),
        )
    return foundation_base_names


USE_CASE_INPUT_BASE_NAMES = {"BaseCommand", "BaseQuery"}
USE_CASE_INPUT_ARGUMENTS = {"command", "query"}


def test_core_inner_packages_do_not_import_outer_layers_or_io_libraries() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/*/**/*.py"):
        if path.name == "__init__.py":
            continue
        relative_parts = path.relative_to(SRC_ROOT / "core").parts
        if len(relative_parts) < 2 or relative_parts[1] not in INNER_PACKAGE_NAMES:
            continue
        for module in _imports(path):
            parts = _module_parts(module)
            if "delivery" in parts or "infrastructure" in parts:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
            if "ioc" in parts:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
            if parts and parts[0] in {"fastapi", "httpx", "redis", "sqlalchemy"}:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")

    assert violations == []


def test_core_does_not_contain_delivery_packages() -> None:
    assert list((SRC_ROOT / "core").glob("*/delivery")) == []


def test_use_cases_do_not_import_or_return_entities() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        if path.name == "__init__.py":
            continue
        for module in _imports(path):
            if "entities" in module.split("."):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")

        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == "execute":
                return_annotation = _annotation_name(node.returns)
                if "Entity" in return_annotation:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)} execute returns {return_annotation}",
                    )

    assert violations == []


def test_use_cases_return_dtos() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == "execute":
                return_annotation = _annotation_name(node.returns)
                if "DTO" not in return_annotation:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)} execute returns {return_annotation}",
                    )

    assert violations == []


def test_use_case_inputs_are_local_commands_or_queries() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        if path.name == "__init__.py":
            continue
        tree = _tree(path)
        aliases = _import_aliases(tree)
        local_input_classes: dict[str, str] = {}
        use_case_classes: list[ast.ClassDef] = []
        consumed_input_classes: set[str] = set()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = _class_direct_base_names(node, aliases)
            input_base_name = next(
                (base_name for base_name in base_names if base_name in USE_CASE_INPUT_BASE_NAMES),
                None,
            )
            if input_base_name is not None:
                local_input_classes[node.name] = input_base_name
            if "BaseUseCase" in base_names:
                use_case_classes.append(node)

        for use_case_class in use_case_classes:
            execute_methods = [
                node
                for node in use_case_class.body
                if (
                    isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
                    and node.name == "execute"
                )
            ]
            if len(execute_methods) != 1:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{use_case_class.name}")
                continue

            execute = execute_methods[0]
            args = execute.args
            if (
                len(args.args) != 1
                or args.args[0].arg != "self"
                or args.vararg is not None
                or args.kwarg is not None
                or len(args.kwonlyargs) != 1
                or args.kw_defaults != [None]
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{use_case_class.name}")
                continue

            input_arg = args.kwonlyargs[0]
            input_name = input_arg.arg
            input_annotation = _annotation_name(input_arg.annotation, aliases)
            input_base_name = local_input_classes.get(input_annotation)
            if input_name not in USE_CASE_INPUT_ARGUMENTS or input_base_name is None:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{use_case_class.name}")
                continue
            consumed_input_classes.add(input_annotation)
            if input_name == "command" and input_base_name != "BaseCommand":
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{use_case_class.name}")
            if input_name == "query" and input_base_name != "BaseQuery":
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{use_case_class.name}")

        for input_class_name in sorted(set(local_input_classes) - consumed_input_classes):
            violations.append(f"{path.relative_to(PROJECT_ROOT)}:{input_class_name} is unused")

    assert violations == []


def test_non_foundation_source_classes_have_explicit_base_classes() -> None:
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.bases:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")

    assert violations == []


def test_foundation_classes_have_scoped_docstrings_with_examples() -> None:
    violations = []
    for path in (SRC_ROOT / "foundation").rglob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _has_scoped_example_docstring(node):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")

    assert violations == []


def test_non_foundation_classes_have_scoped_docstrings_with_examples() -> None:
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _has_scoped_example_docstring(node):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")

    assert violations == []


def test_service_classes_use_service_suffix() -> None:
    service_paths = [
        *(SRC_ROOT / "core").glob("*/services/**/*.py"),
        *(SRC_ROOT / "delivery").glob("**/services/**/*.py"),
    ]
    violations = []
    for path in service_paths:
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.endswith("Service"):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")

    assert violations == []


def test_classes_use_suffix_from_base_class_category() -> None:
    class_base_name_index = _class_base_name_index()
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            direct_base_names = _class_direct_base_names(node, aliases)
            foundation_base_names = set(direct_base_names)
            for base_name in direct_base_names:
                foundation_base_names.update(
                    _foundation_base_names_for_class(
                        base_name,
                        class_base_name_index,
                    ),
                )
            suffixes = {
                suffix
                for base_name in foundation_base_names
                if (suffix := _class_suffix_from_base(base_name)) is not None
            }
            if not suffixes:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} has no recognized "
                    "foundation category",
                )
                continue
            if not any(node.name.endswith(suffix) for suffix in suffixes):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} expected one of "
                    f"{sorted(suffixes)}",
                )

    assert violations == []


def test_non_foundation_classes_do_not_use_raw_common_bases() -> None:
    raw_base_names = {
        "ABC",
        "BaseModel",
        "BaseSettings",
        "DeclarativeBase",
        "Exception",
        "StrEnum",
        "ValueError",
        "object",
    }
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            raw_bases = {_base_name(base, aliases) for base in node.bases} & raw_base_names
            if raw_bases:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} uses {sorted(raw_bases)}",
                )

    assert violations == []


def test_delivery_controllers_do_not_import_infrastructure() -> None:
    violations = []
    for path in (SRC_ROOT / "delivery").glob("**/controllers/**/*.py"):
        if path.name == "__init__.py":
            continue
        for module in _imports(path):
            if "infrastructure" in _module_parts(module):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")

    assert violations == []
```

Add separate tests for:

- delivery controllers do not import infrastructure;
- non-foundation source classes have explicit base classes;
- service classes use the `Service` suffix;
- core services inherit `BasePureService`, `BaseReadService`, or
  `BaseEffectService`, never a generic `BaseService`;
- pure services do not depend on UoWs, repositories, gateways, clients,
  settings, clocks, UUID/random/time, SQLAlchemy, Redis, OpenAI SDK, or HTTP;
- read services do not commit, roll back, call repository mutators, publish
  messages, send email, charge money, or call external write APIs;
- effect services do not inject UoW managers, open UoW scopes, commit, roll
  back, return entities outward, or import delivery/framework code;
- class names use the suffix implied by their most-specific foundation
  ancestry, including intermediate project bases;
- every use case accepts exactly one same-file `Command` or `Query` input;
- every command/query class in a use-case file is consumed by a same-file use
  case;
- command/query classes live with use cases, not under `dtos/`;
- use cases return DTOs and do not import or return entities;
- result DTO classes live under `core/<scope>/dtos/`, not inside use-case
  files;
- capabilities live under `core/<scope>/capabilities/` or stable `shared/`
  locations, direct concrete `BaseCapability` subclasses use the `Capability`
  suffix, narrower `BaseCapability` families use the narrower suffix, and
  capability classes do not pose as helpers, utilities, managers, services,
  repositories, gateways, or use cases;
- gateway ports live under `core/<scope>/gateways/`, directly inherit
  `BaseGateway`, declare external effects in docstrings, and do not return
  entities;
- concrete gateway implementations inherit the scope gateway port and live
  under `core/<scope>/infrastructure/<technology>/`;
- use cases do not return repository result variables directly; wrap repository
  entities in DTO constructors or `DTO.model_validate(...)`;
- query use cases do not call mutating repository methods. Derive mutators from
  repository port methods, treat names such as `get`, `list`, `find`, `count`,
  and `exists` as reads, and flag mutator calls rooted in active UoW
  repositories or injected repository fields;
- root `AGENTS.md` exists, documents project commands plus the core Specx
  boundaries, and only documents `make <target>` commands that exist in the
  Makefile;
- foundation classes have scoped docstrings with concrete examples;
- major non-foundation classes have scoped docstrings with concrete examples;
- non-foundation classes do not directly inherit raw common bases;
- only `ioc`, top-level delivery `__main__.py`/factory modules, and tests use
  `diwire.Container`; catch both `from diwire import Container` and
  `import diwire` aliases used as `diwire.Container`;
- public route paths start with `/api/v1/`;
- SQLAlchemy projects run Alembic migrations in tests instead of calling
  `metadata.create_all` or `drop_all`; use AST call checks for `.create_all()`
  and `.drop_all()`, not substring search;
- SQLAlchemy projects have an Alembic drift check;
- services do not open UoW scopes; use cases own transaction lifecycle and pass
  active UoWs into read/effect services when needed;
- persistence use cases inject `Injected[*UnitOfWorkManager]`, not
  `Provider[UnitOfWork]` and not an active `*UnitOfWork`;
- use cases open at most one UoW manager scope inside `execute(...)`;
- deterministic use cases with no external IO do not need a UoW manager.

## Route Path Guardrail

For a small FastAPI app, a route registration integration test is often clearer
than deep AST inspection:

```python
from diwire import Container
from fastapi import APIRouter

from order_service.delivery.fastapi.controllers.health import HealthController


def test_public_routes_use_full_api_v1_paths(container: Container) -> None:
    router = APIRouter()
    container.resolve(HealthController).register(router)

    route_paths = [
        path
        for route in router.routes
        if (path := getattr(route, "path", None)) is not None
    ]

    assert "/api/v1/health" in route_paths
    assert all(path.startswith("/api/v1/") for path in route_paths)
```

Use this test for controllers registered through classes. Use AST checks when
route registration is spread across many modules or when you need to reject
`APIRouter(prefix="/api/v1")`.

## E2E Tests

Keep e2e tests small:

- app starts;
- health route works;
- one representative happy path crosses HTTP, use case, adapter, and storage.

## Avoid

- Do not duplicate every unit scenario through HTTP.
- Do not make tests depend on implementation-private method names.
- Do not use raw SQLAlchemy sessions in delivery tests.
- Do not use `metadata.create_all`, `drop_all`, or schema bootstrap helpers in
  integration tests. Apply Alembic migrations to temporary databases.
- Do not hide all test setup inside fixtures when explicit setup is clearer.
