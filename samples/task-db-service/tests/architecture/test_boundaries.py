import ast
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src" / "task_db_service"

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
    "DTO",
    "Query",
)
BASE_SUFFIX_OVERRIDES = {
    "ApplicationError": "Error",
    "ApplicationValueError": "ValueError",
    "DeliveryService": "Service",
    "FastAPISchema": "Schema",
    "PureService": "Service",
    "ReadService": "Service",
    "EffectService": "Service",
    "RuntimeSettings": "Settings",
    "SQLAlchemyModel": "Model",
}
USE_CASE_INPUT_BASE_NAMES = {"BaseCommand", "BaseQuery"}
USE_CASE_INPUT_ARGUMENTS = {"command", "query"}
CORE_SERVICE_BASE_NAMES = {"BasePureService", "BaseReadService", "BaseEffectService"}
CAPABILITY_FORBIDDEN_NAME_SUFFIXES = (
    "Dependency",
    "Gateway",
    "Helper",
    "Manager",
    "Repository",
    "Service",
    "Util",
    "Utils",
    "UseCase",
)
GATEWAY_EFFECT_DECLARATION_MARKERS = ("External effect:", "External effects:")
PURE_SERVICE_FORBIDDEN_DEPENDENCY_FRAGMENTS = (
    "UnitOfWorkManager",
    "UnitOfWork",
    "Repository",
    "Gateway",
    "Client",
    "Settings",
    "Clock",
    "UUID",
    "Random",
)
PURE_SERVICE_FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "httpx",
    "openai",
    "random",
    "redis",
    "requests",
    "sqlalchemy",
    "time",
    "uuid",
}
PURE_SERVICE_FORBIDDEN_IMPORT_PARTS = {
    "delivery",
    "infrastructure",
    "ioc",
    "repositories",
    "settings",
}
READ_SERVICE_FORBIDDEN_CALL_NAMES = {
    "charge",
    "charge_money",
    "commit",
    "publish",
    "publish_event",
    "rollback",
    "send_email",
    "send_message",
}
READ_SERVICE_FORBIDDEN_CALL_PREFIXES = ("charge_", "publish_", "send_")
EFFECT_SERVICE_FORBIDDEN_IMPORT_ROOTS = {"fastapi", "starlette"}
EFFECT_SERVICE_FORBIDDEN_IMPORT_PARTS = {"delivery"}
READ_REPOSITORY_METHOD_NAMES = {"count", "exists", "find", "get", "list", "search"}
READ_REPOSITORY_METHOD_PREFIXES = (
    "count_by_",
    "exists_by_",
    "find_by_",
    "find_for_",
    "get_by_",
    "get_for_",
    "list_by_",
    "list_for_",
    "search_by_",
)
SCHEMA_BOOTSTRAP_METHOD_NAMES = {"create_all", "drop_all"}
MAKE_COMMAND_PATTERN = re.compile(r"`make\s+([a-zA-Z0-9_.-]+)(?:\s|`)")
MAKE_TARGET_PATTERN = re.compile(r"^([a-zA-Z0-9_.-]+):(?:\s|$)", re.MULTILINE)


def _source_paths() -> list[Path]:
    return [path for path in SRC_ROOT.rglob("*.py") if path.name != "__init__.py"]


def _core_service_paths() -> list[Path]:
    return [
        path
        for path in (SRC_ROOT / "core").glob("*/services/**/*.py")
        if path.name != "__init__.py"
    ]


def _core_paths() -> list[Path]:
    return [path for path in (SRC_ROOT / "core").glob("*/*/**/*.py") if path.name != "__init__.py"]


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
                f"{module_name}{separator}{alias.name}" for alias in node.names if alias.name != "*"
            )
    return modules


def _module_parts(module: str) -> tuple[str, ...]:
    return tuple(part for part in module.split(".") if part)


def _makefile_targets() -> set[str]:
    text = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    return {
        match.group(1)
        for match in MAKE_TARGET_PATTERN.finditer(text)
        if not match.group(1).startswith(".")
    }


def _documented_make_targets(text: str) -> set[str]:
    return set(MAKE_COMMAND_PATTERN.findall(text))


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name.split(".")[-1]
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
    return aliases


def _uses_diwire_container(tree: ast.Module) -> bool:
    diwire_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "diwire":
                    diwire_aliases.add(alias.asname or alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module == "diwire"
            and any(alias.name == "Container" for alias in node.names)
        ):
            return True
    return any(
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in diwire_aliases
        and node.attr == "Container"
        for node in ast.walk(tree)
    )


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


def _class_suffix_from_base(base_name: str) -> str | None:
    normalized_base_name = base_name.removeprefix("Base")
    if normalized_base_name in BASE_SUFFIX_OVERRIDES:
        return BASE_SUFFIX_OVERRIDES[normalized_base_name]
    return next(
        (suffix for suffix in BASE_SUFFIXES if normalized_base_name.endswith(suffix)),
        None,
    )


def _capability_family_suffix_from_base(
    base_name: str,
    class_base_name_index: dict[str, set[str]],
) -> str | None:
    if base_name == "BaseCapability" or not base_name.startswith("Base"):
        return None
    if "BaseCapability" not in _foundation_base_names_for_class(
        base_name,
        class_base_name_index,
    ):
        return None
    return base_name.removeprefix("Base")


def _category_suffix_from_base(
    base_name: str,
    class_base_name_index: dict[str, set[str]],
) -> str | None:
    return _class_suffix_from_base(base_name) or _capability_family_suffix_from_base(
        base_name,
        class_base_name_index,
    )


def _has_scoped_example_docstring(node: ast.ClassDef) -> bool:
    docstring = ast.get_docstring(node)
    if docstring is None or "Example:" not in docstring:
        return False
    scope, _separator, example = docstring.partition("Example:")
    if any(line.strip() in {"...", "pass"} for line in example.splitlines()):
        return False
    example_lines = [line.strip() for line in example.splitlines() if line.strip()]
    return scope.strip() != "" and example_lines != []


def _declares_external_effect(node: ast.ClassDef) -> bool:
    docstring = ast.get_docstring(node)
    return docstring is not None and any(
        marker in docstring for marker in GATEWAY_EFFECT_DECLARATION_MARKERS
    )


def _field_aliases_for_self_fields(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    field_names: set[str],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            source_field = _self_attribute_root_name(node.value)
            if source_field not in field_names:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    aliases[target.id] = source_field
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            source_field = _self_attribute_root_name(node.value)
            if source_field in field_names:
                aliases[node.target.id] = source_field
    return aliases


def _context_self_fields(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    field_names: set[str],
) -> set[str]:
    fields: set[str] = set()
    field_aliases = _field_aliases_for_self_fields(function, field_names)
    for node in ast.walk(function):
        if not isinstance(node, ast.AsyncWith):
            continue
        for item in node.items:
            field_name = _self_attribute_root_name(item.context_expr)
            if field_name in field_names:
                fields.add(field_name)
                continue
            root_name = _root_name(item.context_expr)
            if root_name in field_aliases:
                fields.add(field_aliases[root_name])
    return fields


def _context_self_field_count(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    field_names: set[str],
) -> int:
    count = 0
    field_aliases = _field_aliases_for_self_fields(function, field_names)
    for node in ast.walk(function):
        if not isinstance(node, ast.AsyncWith):
            continue
        for item in node.items:
            field_name = _self_attribute_root_name(item.context_expr)
            root_name = _root_name(item.context_expr)
            if field_name in field_names or root_name in field_aliases:
                count += 1
    return count


def _uow_manager_context_fields(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    manager_fields: set[str],
) -> set[str]:
    return _context_self_fields(function, manager_fields)


def _uow_manager_context_count(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    manager_fields: set[str],
) -> int:
    return _context_self_field_count(function, manager_fields)


def _injected_type_name(annotation: ast.expr | None, aliases: dict[str, str]) -> str:
    if not isinstance(annotation, ast.Subscript):
        return ""
    if _annotation_name(annotation.value, aliases) != "Injected":
        return ""
    return _annotation_name(annotation.slice, aliases)


def _root_name(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return _root_name(expression.value)
    if isinstance(expression, ast.Subscript):
        return _root_name(expression.value)
    if isinstance(expression, ast.Call):
        return _root_name(expression.func)
    return None


def _call_is_rooted_in_names(call: ast.Call, names: set[str]) -> bool:
    return isinstance(call.func, ast.Attribute) and _root_name(call.func.value) in names


def _expression_is_rooted_in_names(expression: ast.expr | None, names: set[str]) -> bool:
    return expression is not None and _root_name(expression) in names


def _self_attribute_root_name(expression: ast.expr | None) -> str | None:
    if isinstance(expression, ast.Attribute):
        if isinstance(expression.value, ast.Name) and expression.value.id == "self":
            return expression.attr
        return _self_attribute_root_name(expression.value)
    if isinstance(expression, ast.Subscript):
        return _self_attribute_root_name(expression.value)
    if isinstance(expression, ast.Call):
        return _self_attribute_root_name(expression.func)
    return None


def _expression_is_rooted_in_self_attributes(
    expression: ast.expr | None,
    attribute_names: set[str],
) -> bool:
    return expression is not None and _self_attribute_root_name(expression) in attribute_names


def _call_is_rooted_in_self_attributes(call: ast.Call, attribute_names: set[str]) -> bool:
    return isinstance(call.func, ast.Attribute) and _expression_is_rooted_in_self_attributes(
        call.func.value,
        attribute_names,
    )


def _call_from_expression(expression: ast.expr | None) -> ast.Call | None:
    if isinstance(expression, ast.Await):
        expression = expression.value
    if isinstance(expression, ast.Call):
        return expression
    return None


def _active_uow_names(function: ast.AsyncFunctionDef | ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.AsyncWith):
            continue
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                names.add(item.optional_vars.id)
    return names


def _unit_of_work_argument_names(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> set[str]:
    names: set[str] = set()
    arguments = [*function.args.args, *function.args.kwonlyargs]
    for argument in arguments:
        if argument.arg == "self":
            continue
        annotation_name = _annotation_name(argument.annotation, aliases)
        if "UnitOfWork" in annotation_name or argument.arg in {"unit_of_work", "uow"}:
            names.add(argument.arg)
    return names


def _active_repository_names(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    *,
    root_names: set[str] | None = None,
    self_attribute_names: set[str] | None = None,
) -> set[str]:
    root_names = root_names or set()
    self_attribute_names = self_attribute_names or set()
    repository_names: set[str] = set()
    changed = True
    while changed:
        changed = False
        known_names = _active_uow_names(function) | root_names | repository_names
        for node in ast.walk(function):
            value: ast.expr | None
            targets: list[ast.expr]
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            else:
                continue
            if not (
                _expression_is_rooted_in_names(value, known_names)
                or _expression_is_rooted_in_self_attributes(value, self_attribute_names)
            ):
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in repository_names:
                    repository_names.add(target.id)
                    changed = True
    return repository_names


def _repository_result_variable_names(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    *,
    root_names: set[str] | None = None,
    self_attribute_names: set[str] | None = None,
) -> set[str]:
    root_names = root_names or set()
    self_attribute_names = self_attribute_names or set()
    repository_roots = (
        _active_uow_names(function)
        | root_names
        | _active_repository_names(
            function,
            root_names=root_names,
            self_attribute_names=self_attribute_names,
        )
    )
    repository_results: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(function):
            value: ast.expr | None
            targets: list[ast.expr]
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            else:
                continue
            call = _call_from_expression(value)
            is_repository_result = call is not None and (
                _call_is_rooted_in_names(call, repository_roots)
                or _call_is_rooted_in_self_attributes(call, self_attribute_names)
            )
            is_repository_result_alias = _expression_is_rooted_in_names(
                value,
                repository_results,
            )
            if not is_repository_result and not is_repository_result_alias:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in repository_results:
                    repository_results.add(target.id)
                    changed = True
    return repository_results


def _repository_mutator_method_names() -> set[str]:
    method_names: set[str] = set()
    for path in (SRC_ROOT / "core").glob("*/repositories/*repository.py"):
        for node in ast.walk(_tree(path)):
            if (
                isinstance(node, ast.AsyncFunctionDef)
                and not node.name.startswith("_")
                and not _is_read_repository_method_name(node.name)
            ):
                method_names.add(node.name)
    return method_names


def _is_read_repository_method_name(method_name: str) -> bool:
    return method_name in READ_REPOSITORY_METHOD_NAMES or method_name.startswith(
        READ_REPOSITORY_METHOD_PREFIXES,
    )


def _is_schema_bootstrap_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Attribute) and call.func.attr in SCHEMA_BOOTSTRAP_METHOD_NAMES


def _class_direct_base_names(node: ast.ClassDef, aliases: dict[str, str]) -> set[str]:
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
    foundation_base_names: set[str] = set()
    for base_name in class_base_name_index.get(class_name, set()):
        if _class_suffix_from_base(base_name) is not None:
            foundation_base_names.add(base_name)
        foundation_base_names.update(
            _foundation_base_names_for_class(
                base_name,
                class_base_name_index,
                visited=visited,
            ),
        )
    return foundation_base_names


def _class_has_foundation_base(
    class_name: str,
    foundation_base_name: str,
    class_base_name_index: dict[str, set[str]],
) -> bool:
    return foundation_base_name in _foundation_base_names_for_class(
        class_name,
        class_base_name_index,
    )


def _nearest_foundation_base_names_for_class(
    class_name: str,
    class_base_name_index: dict[str, set[str]],
    *,
    visited: set[str] | None = None,
) -> set[str]:
    visited = visited or set()
    if class_name in visited:
        return set()
    visited.add(class_name)
    nearest_base_names: set[str] = set()
    for base_name in class_base_name_index.get(class_name, set()):
        if _category_suffix_from_base(base_name, class_base_name_index) is not None:
            nearest_base_names.add(base_name)
            continue
        nearest_base_names.update(
            _nearest_foundation_base_names_for_class(
                base_name,
                class_base_name_index,
                visited=visited,
            ),
        )
    return nearest_base_names


def _execute_methods_with_classes(
    tree: ast.Module,
) -> list[tuple[ast.ClassDef, ast.AsyncFunctionDef | ast.FunctionDef]]:
    execute_methods: list[tuple[ast.ClassDef, ast.AsyncFunctionDef | ast.FunctionDef]] = []
    for class_node in ast.walk(tree):
        if not isinstance(class_node, ast.ClassDef):
            continue
        for child in class_node.body:
            if (
                isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef)
                and child.name == "execute"
            ):
                execute_methods.append((class_node, child))
    return execute_methods


def _class_injected_repository_field_names(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
    class_base_name_index: dict[str, set[str]],
) -> set[str]:
    field_names: set[str] = set()
    for child in class_node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
            continue
        dependency_name = _injected_type_name(child.annotation, aliases) or _annotation_name(
            child.annotation,
            aliases,
        )
        if dependency_name.endswith("Repository") or _class_has_foundation_base(
            dependency_name,
            "BaseRepository",
            class_base_name_index,
        ):
            field_names.add(child.target.id)
    return field_names


def _class_injected_unit_of_work_manager_field_names(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
) -> set[str]:
    field_names: set[str] = set()
    for child in class_node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
            continue
        injected_type_name = _injected_type_name(child.annotation, aliases)
        if injected_type_name.endswith("UnitOfWorkManager"):
            field_names.add(child.target.id)
    return field_names


def _class_unit_of_work_field_names(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
) -> set[str]:
    field_names: set[str] = set()
    for child in class_node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
            continue
        dependency_name = _injected_type_name(child.annotation, aliases) or _annotation_name(
            child.annotation,
            aliases,
        )
        if "UnitOfWork" in dependency_name:
            field_names.add(child.target.id)
    return field_names


def _class_dependency_annotations(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
) -> list[str]:
    annotations: list[str] = []
    for child in class_node.body:
        if isinstance(child, ast.AnnAssign):
            annotations.append(
                _injected_type_name(child.annotation, aliases)
                or _annotation_name(child.annotation, aliases)
            )
        if isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
            arguments = [*child.args.args, *child.args.kwonlyargs]
            for argument in arguments:
                if argument.arg == "self":
                    continue
                annotations.append(_annotation_name(argument.annotation, aliases))
            annotations.append(_annotation_name(child.returns, aliases))
    return [annotation for annotation in annotations if annotation]


def _class_has_any_foundation_base(
    class_name: str,
    foundation_base_names: set[str],
    class_base_name_index: dict[str, set[str]],
) -> bool:
    return any(
        _class_has_foundation_base(class_name, foundation_base_name, class_base_name_index)
        for foundation_base_name in foundation_base_names
    )


def _forbidden_dependency_fragments(
    dependency_name: str,
    fragments: tuple[str, ...],
) -> list[str]:
    lowered_dependency_name = dependency_name.lower()
    return [fragment for fragment in fragments if fragment.lower() in lowered_dependency_name]


def _calls_forbidden_method(
    call: ast.Call,
    method_names: set[str],
    prefixes: tuple[str, ...],
) -> bool:
    return isinstance(call.func, ast.Attribute) and (
        call.func.attr in method_names or call.func.attr.startswith(prefixes)
    )


def _module_has_forbidden_parts(
    module: str,
    *,
    roots: set[str],
    parts: set[str],
) -> bool:
    module_parts = _module_parts(module)
    return bool(module_parts) and (
        module_parts[0] in roots or any(part in parts for part in module_parts)
    )


def test_core_inner_packages_do_not_import_outer_layers_or_io_libraries() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/*/**/*.py"):
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


def test_scope_infrastructure_does_not_import_delivery() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/infrastructure/**/*.py"):
        for module in _imports(path):
            if "delivery" in _module_parts(module):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
    assert violations == []


def test_delivery_controllers_do_not_import_infrastructure() -> None:
    violations = []
    for path in (SRC_ROOT / "delivery").glob("**/controllers/**/*.py"):
        for module in _imports(path):
            if "infrastructure" in _module_parts(module):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
    assert violations == []


def test_core_does_not_contain_delivery_packages() -> None:
    assert list((SRC_ROOT / "core").glob("*/delivery")) == []


def test_use_cases_do_not_import_or_return_entities() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "entities" in alias.name.split("."):
                        violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                module_parts = module.split(".")
                imports_entity_module = "entities" in module_parts
                imports_entity_name = any(alias.name.endswith("Entity") for alias in node.names)
                if imports_entity_module or (node.level > 0 and imports_entity_name):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")

        for class_node, execute in _execute_methods_with_classes(tree):
            repository_attribute_names = _class_injected_repository_field_names(
                class_node,
                aliases,
                class_base_name_index,
            )
            return_annotation = _annotation_name(execute.returns, aliases)
            if "Entity" in return_annotation:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} execute returns {return_annotation}",
                )
            repository_results = _repository_result_variable_names(
                execute,
                self_attribute_names=repository_attribute_names,
            )
            for return_node in ast.walk(execute):
                if not isinstance(return_node, ast.Return):
                    continue
                if (
                    isinstance(return_node.value, ast.Name)
                    and return_node.value.id in repository_results
                ):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)} returns repository result directly",
                    )
                if _expression_is_rooted_in_names(return_node.value, repository_results):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)} returns repository result expression",
                    )
                call = _call_from_expression(return_node.value)
                if call is not None and _call_is_rooted_in_self_attributes(
                    call,
                    repository_attribute_names,
                ):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)} returns repository call directly",
                    )
    assert violations == []


def test_use_cases_return_dtos() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for _class_node, execute in _execute_methods_with_classes(tree):
            return_annotation = _annotation_name(execute.returns, aliases)
            if "DTO" not in return_annotation:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} execute returns {return_annotation}",
                )
    assert violations == []


def test_result_dto_classes_live_under_scope_dtos_package() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in (SRC_ROOT / "core").glob("*/**/*.py"):
        relative_parts = path.relative_to(SRC_ROOT / "core").parts
        if len(relative_parts) < 2:
            continue
        tree = _tree(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            nearest_foundation_bases = _nearest_foundation_base_names_for_class(
                node.name,
                class_base_name_index,
            )
            is_dto = any(
                _class_suffix_from_base(base_name) == "DTO"
                for base_name in nearest_foundation_bases
            )
            if is_dto and relative_parts[1] != "dtos":
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_use_case_inputs_are_local_commands_or_queries() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
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
            if "BaseUseCase" in base_names or _class_has_foundation_base(
                node.name,
                "BaseUseCase",
                class_base_name_index,
            ):
                use_case_classes.append(node)

        for use_case_class in use_case_classes:
            execute_methods = [
                node
                for node in use_case_class.body
                if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
                and node.name == "execute"
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


def test_command_and_query_classes_live_with_use_cases() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("**/*.py"):
        if "use_cases" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = _class_direct_base_names(node, aliases)
                if base_names & USE_CASE_INPUT_BASE_NAMES:
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_capabilities_live_in_expected_packages_and_use_expected_suffixes() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        relative_parts = path.relative_to(SRC_ROOT).parts
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _class_has_foundation_base(
                node.name,
                "BaseCapability",
                class_base_name_index,
            ):
                continue
            if relative_parts[0] == "core":
                inner_package = relative_parts[2] if len(relative_parts) > 2 else ""
                if inner_package != "capabilities":
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.name} "
                        "capability outside capabilities",
                    )
            elif relative_parts[0] != "shared":
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} capability outside core/shared",
                )
            direct_base_names = _class_direct_base_names(node, aliases)
            if "BaseCapability" in direct_base_names and not node.name.endswith("Capability"):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} "
                    "direct BaseCapability subclass must end with Capability",
                )
    assert violations == []


def test_capabilities_do_not_own_workflows_or_other_port_roles() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
            if not _class_has_foundation_base(
                class_node.name,
                "BaseCapability",
                class_base_name_index,
            ):
                continue
            capability_role_name = class_node.name.removesuffix("Capability")
            forbidden_suffix = next(
                (
                    suffix
                    for suffix in CAPABILITY_FORBIDDEN_NAME_SUFFIXES
                    if class_node.name.endswith(suffix) or capability_role_name.endswith(suffix)
                ),
                None,
            )
            if forbidden_suffix is not None:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                    f"uses {forbidden_suffix} role name",
                )
            for incompatible_base_name in ("BaseRepository", "BaseGateway", "BaseUseCase"):
                if _class_has_foundation_base(
                    class_node.name,
                    incompatible_base_name,
                    class_base_name_index,
                ):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                        f"also inherits {incompatible_base_name}",
                    )
            unit_of_work_fields = _class_unit_of_work_field_names(class_node, aliases)
            if unit_of_work_fields:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                    f"depends on {sorted(unit_of_work_fields)}",
                )
            for child in class_node.body:
                if not isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
                    continue
                context_fields = _context_self_fields(child, unit_of_work_fields)
                if context_fields:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                        f"opens {sorted(context_fields)}",
                    )
    assert violations == []


def test_gateway_ports_and_implementations_live_in_expected_packages() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _core_paths():
        relative_parts = path.relative_to(SRC_ROOT / "core").parts
        if len(relative_parts) < 2:
            continue
        inner_package = relative_parts[1]
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _class_has_foundation_base(
                node.name,
                "BaseGateway",
                class_base_name_index,
            ):
                continue
            direct_base_names = _class_direct_base_names(node, aliases)
            if "BaseGateway" in direct_base_names and inner_package != "gateways":
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} port outside gateways",
                )
            if "BaseGateway" not in direct_base_names and inner_package != "infrastructure":
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} implementation "
                    "outside infrastructure",
                )
    assert violations == []


def test_gateways_declare_external_effects_and_do_not_return_entities() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _core_paths():
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _class_has_foundation_base(
                node.name,
                "BaseGateway",
                class_base_name_index,
            ):
                continue
            if not _declares_external_effect(node):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} missing external effect",
                )
            for child in node.body:
                if not isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
                    continue
                return_annotation = _annotation_name(child.returns, aliases)
                if "Entity" in return_annotation:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.name}.{child.name} "
                        f"returns {return_annotation}",
                    )
    assert violations == []


def test_query_use_cases_do_not_call_repository_mutators() -> None:
    repository_mutator_method_names = _repository_mutator_method_names()
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        local_input_classes = {
            node.name: _class_direct_base_names(node, aliases)
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        }
        for class_node, execute in _execute_methods_with_classes(tree):
            if len(execute.args.kwonlyargs) != 1 or execute.args.kwonlyargs[0].arg != "query":
                continue
            query_annotation = _annotation_name(execute.args.kwonlyargs[0].annotation, aliases)
            if "BaseQuery" not in local_input_classes.get(query_annotation, set()):
                continue
            repository_attribute_names = _class_injected_repository_field_names(
                class_node,
                aliases,
                class_base_name_index,
            )
            repository_roots = _active_uow_names(execute) | _active_repository_names(
                execute,
                self_attribute_names=repository_attribute_names,
            )
            mutator_calls = [
                call.func.attr
                for call in ast.walk(execute)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr in repository_mutator_method_names
                and (
                    _call_is_rooted_in_names(call, repository_roots)
                    or _call_is_rooted_in_self_attributes(call, repository_attribute_names)
                )
            ]
            if mutator_calls:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} calls {sorted(set(mutator_calls))}",
                )
    assert violations == []


def test_non_foundation_source_classes_have_explicit_base_classes() -> None:
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.bases:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_classes_have_scoped_docstrings_with_examples() -> None:
    violations = []
    for path in _source_paths():
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not _has_scoped_example_docstring(node):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_service_classes_use_service_suffix() -> None:
    service_paths = [
        *(SRC_ROOT / "core").glob("*/services/**/*.py"),
        *(SRC_ROOT / "delivery").glob("**/services/**/*.py"),
    ]
    violations = []
    for path in service_paths:
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.endswith("Service"):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_core_services_use_effect_specific_service_bases() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _core_service_paths():
        tree = _tree(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _class_has_any_foundation_base(
                node.name,
                CORE_SERVICE_BASE_NAMES,
                class_base_name_index,
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
    assert violations == []


def test_generic_base_service_is_not_used() -> None:
    violations = []
    for path in _source_paths():
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "BaseService":
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.name}")
            if isinstance(node, ast.ImportFrom):
                imported_names = {alias.name for alias in node.names}
                if "BaseService" in imported_names:
                    violations.append(f"{path.relative_to(PROJECT_ROOT)} imports BaseService")
    assert violations == []


def test_pure_services_do_not_depend_on_io_or_runtime_state() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _core_service_paths():
        tree = _tree(path)
        aliases = _import_aliases(tree)
        pure_service_classes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and _class_has_foundation_base(
                node.name,
                "BasePureService",
                class_base_name_index,
            )
        ]
        if not pure_service_classes:
            continue
        for module in _imports(path):
            if _module_has_forbidden_parts(
                module,
                roots=PURE_SERVICE_FORBIDDEN_IMPORT_ROOTS,
                parts=PURE_SERVICE_FORBIDDEN_IMPORT_PARTS,
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
        for class_node in pure_service_classes:
            for dependency_name in _class_dependency_annotations(class_node, aliases):
                fragments = _forbidden_dependency_fragments(
                    dependency_name,
                    PURE_SERVICE_FORBIDDEN_DEPENDENCY_FRAGMENTS,
                )
                if fragments:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                        f"uses {dependency_name}",
                    )
    assert violations == []


def test_read_services_do_not_perform_writes_or_own_transactions() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    repository_mutator_method_names = _repository_mutator_method_names()
    for path in _core_service_paths():
        tree = _tree(path)
        aliases = _import_aliases(tree)
        read_service_classes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and _class_has_foundation_base(
                node.name,
                "BaseReadService",
                class_base_name_index,
            )
        ]
        for class_node in read_service_classes:
            manager_fields = _class_injected_unit_of_work_manager_field_names(
                class_node,
                aliases,
            )
            if manager_fields:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                    f"injects {sorted(manager_fields)}",
                )
            for child in class_node.body:
                if not isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
                    continue
                unit_of_work_argument_names = _unit_of_work_argument_names(child, aliases)
                repository_roots = unit_of_work_argument_names | _active_repository_names(
                    child,
                    root_names=unit_of_work_argument_names,
                )
                for call in (node for node in ast.walk(child) if isinstance(node, ast.Call)):
                    call_method_name = (
                        call.func.attr if isinstance(call.func, ast.Attribute) else ""
                    )
                    if _calls_forbidden_method(
                        call,
                        READ_SERVICE_FORBIDDEN_CALL_NAMES,
                        READ_SERVICE_FORBIDDEN_CALL_PREFIXES,
                    ):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                            f"calls {call_method_name}",
                        )
                    if (
                        isinstance(call.func, ast.Attribute)
                        and call.func.attr in repository_mutator_method_names
                        and _call_is_rooted_in_names(call, repository_roots)
                    ):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                            f"calls repository mutator {call.func.attr}",
                        )
    assert violations == []


def test_effect_services_do_not_own_transactions_or_import_delivery() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in _core_service_paths():
        tree = _tree(path)
        aliases = _import_aliases(tree)
        effect_service_classes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and _class_has_foundation_base(
                node.name,
                "BaseEffectService",
                class_base_name_index,
            )
        ]
        if not effect_service_classes:
            continue
        for module in _imports(path):
            if _module_has_forbidden_parts(
                module,
                roots=EFFECT_SERVICE_FORBIDDEN_IMPORT_ROOTS,
                parts=EFFECT_SERVICE_FORBIDDEN_IMPORT_PARTS,
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")
        for class_node in effect_service_classes:
            manager_fields = _class_injected_unit_of_work_manager_field_names(
                class_node,
                aliases,
            )
            if manager_fields:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                    f"injects {sorted(manager_fields)}",
                )
            for child in class_node.body:
                if not isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
                    continue
                return_annotation = _annotation_name(child.returns, aliases)
                if "Entity" in return_annotation:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                        f"returns {return_annotation}",
                    )
                for call in (node for node in ast.walk(child) if isinstance(node, ast.Call)):
                    if isinstance(call.func, ast.Attribute) and call.func.attr in {
                        "commit",
                        "rollback",
                    }:
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                            f"calls {call.func.attr}",
                        )
    assert violations == []


def test_classes_use_suffix_from_most_specific_foundation_category() -> None:
    class_base_name_index = _class_base_name_index()
    violations = []
    for path in _source_paths():
        if "foundation" in path.relative_to(SRC_ROOT).parts:
            continue
        tree = _tree(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            foundation_base_names = _nearest_foundation_base_names_for_class(
                node.name,
                class_base_name_index,
            )
            suffixes = {
                suffix
                for base_name in foundation_base_names
                if (suffix := _category_suffix_from_base(base_name, class_base_name_index))
                is not None
            }
            if not suffixes:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} has no recognized category",
                )
                continue
            if not any(node.name.endswith(suffix) for suffix in suffixes):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.name} expected {sorted(suffixes)}",
                )
    assert violations == []


def test_non_foundation_classes_do_not_use_raw_common_bases() -> None:
    raw_base_names = {
        "ABC",
        "BaseModel",
        "BaseSettings",
        "DeclarativeBase",
        "Exception",
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


def test_only_ioc_delivery_app_and_tests_import_container() -> None:
    violations = []
    for path in _source_paths():
        tree = _tree(path)
        if not _uses_diwire_container(tree):
            continue
        relative = path.relative_to(SRC_ROOT)
        allowed = (
            relative == Path("ioc/container.py")
            or relative == Path("delivery/fastapi/__main__.py")
            or relative == Path("delivery/fastapi/factory.py")
        )
        if not allowed:
            violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert violations == []


def test_public_routes_use_full_api_v1_paths() -> None:
    violations = []
    for path in (SRC_ROOT / "delivery").glob("**/controllers/**/*.py"):
        tree = _tree(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_api_route":
                continue
            path_keyword = next(
                (keyword for keyword in node.keywords if keyword.arg == "path"),
                None,
            )
            if path_keyword is None or not isinstance(path_keyword.value, ast.Constant):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} has dynamic route path")
                continue
            route_path = path_keyword.value.value
            if not isinstance(route_path, str) or not route_path.startswith("/api/v1/"):
                violations.append(f"{path.relative_to(PROJECT_ROOT)} uses {route_path!r}")
    assert violations == []


def test_no_schema_bootstrap_calls_in_source_or_tests() -> None:
    violations = []
    for root in (SRC_ROOT, PROJECT_ROOT / "tests"):
        for path in root.rglob("*.py"):
            tree = _tree(path)
            if any(
                _is_schema_bootstrap_call(node)
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
            ):
                violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert violations == []


def test_root_agents_md_documents_project_commands_and_boundaries() -> None:
    text = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    required_fragments = {
        "Package lives under `src/task_db_service`",
        "FastAPI entrypoint: `task_db_service.delivery.fastapi.__main__:app`",
        "make check",
        "make lint",
        "make test",
        "make migration-check",
        "make makemigrations",
        "BaseCapability",
        "BaseGateway",
        "BasePureService",
        "BaseReadService",
        "BaseEffectService",
        "Use cases return DTOs, not entities",
        "Query use cases must not call repository mutators",
        "Do not use `create_all()` or `drop_all()`",
    }

    missing_fragments = sorted(fragment for fragment in required_fragments if fragment not in text)
    missing_make_targets = sorted(_documented_make_targets(text) - _makefile_targets())

    assert missing_fragments == []
    assert missing_make_targets == []


def test_services_do_not_open_unit_of_work_scopes() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/services/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
            unit_of_work_fields = _class_unit_of_work_field_names(class_node, aliases)
            if not unit_of_work_fields:
                continue
            for child in class_node.body:
                if not isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
                    continue
                context_fields = _context_self_fields(child, unit_of_work_fields)
                if context_fields:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} "
                        f"opens {sorted(context_fields)}",
                    )
    assert violations == []


def test_use_cases_open_at_most_one_unit_of_work_scope() -> None:
    violations = []
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for class_node, execute in _execute_methods_with_classes(tree):
            manager_fields = _class_injected_unit_of_work_manager_field_names(
                class_node,
                aliases,
            )
            count = _uow_manager_context_count(execute, manager_fields)
            if count > 1:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} opens {count} UoWs")
    assert violations == []


def test_use_cases_inject_unit_of_work_managers() -> None:
    violations = []
    class_base_name_index = _class_base_name_index()
    for path in (SRC_ROOT / "core").glob("*/use_cases/**/*.py"):
        tree = _tree(path)
        aliases = _import_aliases(tree)
        for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
            base_names = _class_direct_base_names(class_node, aliases)
            if "BaseUseCase" not in base_names and not _class_has_foundation_base(
                class_node.name,
                "BaseUseCase",
                class_base_name_index,
            ):
                continue
            injected_manager_fields = _class_injected_unit_of_work_manager_field_names(
                class_node,
                aliases,
            )
            bad_dependency_fields: list[str] = []
            for child in class_node.body:
                if not isinstance(child, ast.AnnAssign):
                    continue
                annotation_name = _annotation_name(child.annotation, aliases)
                injected_type_name = _injected_type_name(child.annotation, aliases)
                field_name = child.target.id if isinstance(child.target, ast.Name) else ""
                if "Provider" in annotation_name:
                    bad_dependency_fields.append(f"{field_name}:{annotation_name}")
                if "UnitOfWork" in annotation_name and "UnitOfWorkManager" not in annotation_name:
                    bad_dependency_fields.append(f"{field_name}:{annotation_name}")
                if "UnitOfWorkManager" in annotation_name:
                    if injected_type_name.endswith("UnitOfWorkManager"):
                        continue
                    bad_dependency_fields.append(f"{field_name}:{annotation_name}")
            for child in class_node.body:
                if (
                    isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef)
                    and child.name == "execute"
                ):
                    context_fields = _uow_manager_context_fields(child, injected_manager_fields)
                    unknown_context_fields = context_fields - injected_manager_fields
                    if unknown_context_fields:
                        bad_dependency_fields.append(
                            f"opens non-injected manager fields {sorted(unknown_context_fields)}",
                        )
                    if injected_manager_fields and not context_fields:
                        bad_dependency_fields.append("injects UoW manager but does not open it")
            if bad_dependency_fields:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{class_node.name} {bad_dependency_fields}",
                )
    assert violations == []


def test_ioc_container_does_not_register_active_unit_of_work() -> None:
    path = SRC_ROOT / "ioc" / "container.py"
    tree = _tree(path)
    aliases = _import_aliases(tree)
    violations = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "diwire"
            and any(
                aliases.get(alias.asname or alias.name, alias.name) == "Lifetime"
                for alias in node.names
            )
        ):
            violations.append("imports Lifetime")
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add":
            continue
        provides = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "provides"),
            None,
        )
        provides_name = _annotation_name(provides, aliases)
        if provides_name.endswith("UnitOfWork") and not provides_name.endswith("UnitOfWorkManager"):
            violations.append(f"registers active {provides_name}")
    assert violations == []


def test_init_files_are_empty() -> None:
    violations = [
        path.relative_to(PROJECT_ROOT)
        for path in SRC_ROOT.rglob("__init__.py")
        if path.read_text(encoding="utf-8") != ""
    ]
    assert violations == []
