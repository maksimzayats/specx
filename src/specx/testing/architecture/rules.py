from __future__ import annotations

import ast
from pathlib import Path

from specx.testing.architecture.context import (
    CAPABILITY_FORBIDDEN_NAME_SUFFIXES,
    CORE_SERVICE_BASE_NAMES,
    EFFECT_SERVICE_FORBIDDEN_IMPORT_PARTS,
    EFFECT_SERVICE_FORBIDDEN_IMPORT_ROOTS,
    INNER_PACKAGE_NAMES,
    PURE_SERVICE_FORBIDDEN_DEPENDENCY_FRAGMENTS,
    PURE_SERVICE_FORBIDDEN_IMPORT_PARTS,
    PURE_SERVICE_FORBIDDEN_IMPORT_ROOTS,
    READ_SERVICE_FORBIDDEN_CALL_NAMES,
    READ_SERVICE_FORBIDDEN_CALL_PREFIXES,
    USE_CASE_INPUT_ARGUMENTS,
    USE_CASE_INPUT_BASE_NAMES,
    ArchitectureContext,
    active_repository_names,
    active_uow_names,
    active_uow_names_from_manager_fields,
    annotation_name,
    attribute_chain,
    base_name,
    call_from_expression,
    call_is_rooted_in_names,
    call_is_rooted_in_self_attributes,
    calls_forbidden_method,
    category_suffix_from_base,
    class_base_name_index,
    class_dependency_annotations,
    class_direct_base_names,
    class_has_any_foundation_base,
    class_has_foundation_base,
    class_injected_repository_field_names,
    class_injected_unit_of_work_manager_field_names,
    class_suffix_from_base,
    class_unit_of_work_field_names,
    context_self_fields,
    declares_external_effect,
    documented_make_targets,
    execute_methods_with_classes,
    expression_is_rooted_in_names,
    forbidden_dependency_fragments,
    has_scoped_example_docstring,
    injected_type_name,
    is_schema_bootstrap_call,
    module_has_forbidden_parts,
    module_parts,
    nearest_foundation_base_names_for_class,
    repository_mutator_method_names,
    repository_result_variable_names,
    unit_of_work_argument_names,
    uow_manager_context_count,
    uow_manager_context_fields,
    uses_diwire_container,
)
from specx.testing.architecture.models import RuleIdentifier, SpecxArchitectureViolation
from specx.testing.architecture.rule import BaseRule
from specx.testing.architecture.rule_id import SpecxRuleId

ArchitectureRuleBase = BaseRule[
    SpecxRuleId,
    ArchitectureContext,
    SpecxArchitectureViolation,
]

USE_CASE_FORBIDDEN_INFRASTRUCTURE_DEPENDENCY_NAMES = frozenset(
    {
        "AsyncConnection",
        "AsyncEngine",
        "AsyncSession",
        "Connection",
        "Engine",
        "Session",
        "SQLAlchemySessionFactory",
        "async_sessionmaker",
        "sessionmaker",
    }
)
CORE_BEHAVIOR_TEST_PACKAGE_NAMES = frozenset({"capabilities", "services", "use_cases"})


def _violation(
    rule_id: RuleIdentifier,
    *,
    message: str,
    path: Path | None = None,
    symbol: str | None = None,
    node: ast.AST | None = None,
) -> SpecxArchitectureViolation:
    return SpecxArchitectureViolation(
        rule_id=rule_id,
        message=message,
        path=path,
        symbol=symbol,
        line=getattr(node, "lineno", None),
        column=(getattr(node, "col_offset", -1) + 1 if hasattr(node, "col_offset") else None),
    )


class CoreInnerPackagesDoNotImportOuterLayersOrIOLibrariesRule(ArchitectureRuleBase):
    """Keep inner core packages free from delivery, infrastructure, IOC, and IO imports.

    This protects core application code from framework and technical dependencies
    that should stay at the delivery, infrastructure, or composition edge.
    """

    id: SpecxRuleId = SpecxRuleId.CORE_INNER_PACKAGES_DO_NOT_IMPORT_OUTER_LAYERS_OR_IO_LIBRARIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/*/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            relative_parts = path.relative_to(context.src_root / "core").parts
            if len(relative_parts) < 2 or relative_parts[1] not in INNER_PACKAGE_NAMES:
                continue
            for module in context.imports(path):
                parts = module_parts(module)
                if "delivery" in parts or "infrastructure" in parts:
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
                if "ioc" in parts:
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
                if parts and parts[0] in {"fastapi", "httpx", "httpx2", "redis", "sqlalchemy"}:
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
        return tuple(violations)


class ScopeInfrastructureDoesNotImportDeliveryRule(ArchitectureRuleBase):
    """Prevent scope infrastructure adapters from depending on delivery code.

    Scope infrastructure can use technical libraries and core contracts, but it
    must not couple adapters back to HTTP controllers, schemas, or app factories.
    """

    id: SpecxRuleId = SpecxRuleId.SCOPE_INFRASTRUCTURE_DOES_NOT_IMPORT_DELIVERY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/infrastructure/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            for module in context.imports(path):
                if "delivery" in module_parts(module):
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
        return tuple(violations)


class DeliveryControllersDoNotImportInfrastructureRule(ArchitectureRuleBase):
    """Keep delivery modules from reaching into scope infrastructure.

    Controllers should translate framework input and call use cases; concrete
    infrastructure should be composed through IOC or delivery app factories.
    Delivery app composition modules may import top-level infrastructure
    resources, but not scope repositories, ORM models, DDL helpers, or concrete
    scope infrastructure adapters.
    """

    id: SpecxRuleId = SpecxRuleId.DELIVERY_CONTROLLERS_DO_NOT_IMPORT_INFRASTRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "delivery").glob("**/controllers/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            for module in _explicit_import_modules(context.tree(path)):
                if "infrastructure" in module_parts(module):
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
        delivery_root = context.src_root / "delivery"
        for filename in ("__main__.py", "factory.py", "lifecycle.py"):
            for path in delivery_root.glob(f"*/{filename}"):
                if path not in context.ast_project.files:
                    continue
                for module in _explicit_import_modules(context.tree(path)):
                    if _is_scope_technical_import(module):
                        violations.append(
                            _violation(self.id, path=path, message=f"imports {module}"),
                        )
        return tuple(violations)


class CoreDoesNotContainDeliveryPackagesRule(ArchitectureRuleBase):
    """Reject delivery packages nested under core scopes.

    Top-level delivery owns framework translation, while core scopes remain
    framework-free application boundaries.
    """

    id: SpecxRuleId = SpecxRuleId.CORE_DOES_NOT_CONTAIN_DELIVERY_PACKAGES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        return tuple(
            _violation(self.id, path=path, message="core scope contains delivery package")
            for path in (context.src_root / "core").glob("*/delivery")
        )


class FoundationImportsUseScopedPackagesRule(ArchitectureRuleBase):
    """Reject imports from the removed alpha-stage `specx.foundation` namespace.

    Specx foundation bases are scoped by architecture layer. Generated services
    should import from `specx.core.foundation`, `specx.delivery.foundation`, or
    `specx.infrastructure.foundation`.
    """

    id: SpecxRuleId = SpecxRuleId.FOUNDATION_IMPORTS_USE_SCOPED_PACKAGES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for root in (context.src_root, context.project_root / "tests"):
            for path in root.rglob("*.py"):
                if path.name == "__init__.py" or path not in context.ast_project.files:
                    continue
                tree = context.tree(path)
                for module in _explicit_import_modules(tree):
                    if module == "specx.foundation" or module.startswith("specx.foundation."):
                        violations.append(
                            _violation(self.id, path=path, message=f"imports {module}")
                        )
        return tuple(violations)


class UseCasesDoNotImportOrReturnEntitiesRule(ArchitectureRuleBase):
    """Prevent use cases from exposing persistence entities as application results.

    Use cases may coordinate repositories internally, but delivery-facing results
    should be DTOs rather than entities or raw repository return values.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_DO_NOT_IMPORT_OR_RETURN_ENTITIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "entities" in alias.name.split("."):
                            violations.append(
                                _violation(self.id, path=path, message=f"imports {alias.name}"),
                            )
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    imports_entity_module = "entities" in module.split(".")
                    imports_entity_name = any(alias.name.endswith("Entity") for alias in node.names)
                    if imports_entity_module or (node.level > 0 and imports_entity_name):
                        violations.append(
                            _violation(self.id, path=path, message=f"imports {module}"),
                        )

            for class_node, execute in execute_methods_with_classes(tree):
                repository_fields = class_injected_repository_field_names(
                    class_node,
                    aliases,
                    base_index,
                )
                return_annotation = annotation_name(execute.returns, aliases)
                if "Entity" in return_annotation:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"execute returns {return_annotation}",
                            symbol=class_node.name,
                        ),
                    )
                repository_results = repository_result_variable_names(
                    execute,
                    self_attribute_names=repository_fields,
                )
                for return_node in ast.walk(execute):
                    if not isinstance(return_node, ast.Return):
                        continue
                    if (
                        isinstance(return_node.value, ast.Name)
                        and return_node.value.id in repository_results
                    ):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message="returns repository result directly",
                                symbol=class_node.name,
                            ),
                        )
                    if expression_is_rooted_in_names(return_node.value, repository_results):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message="returns repository result expression",
                                symbol=class_node.name,
                            ),
                        )
                    call = call_from_expression(return_node.value)
                    if call is not None and call_is_rooted_in_self_attributes(
                        call, repository_fields
                    ):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message="returns repository call directly",
                                symbol=class_node.name,
                            ),
                        )
        return tuple(violations)


class UseCasesReturnDTOsRule(ArchitectureRuleBase):
    """Require use cases to return DTOs instead of entities or raw values.

    This keeps delivery-facing application results explicit and stable as the
    internal entity or repository model evolves.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_RETURN_DTOS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for class_node, execute in execute_methods_with_classes(tree):
                return_annotation = annotation_name(execute.returns, aliases)
                if "DTO" not in return_annotation:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"execute returns {return_annotation}",
                            symbol=class_node.name,
                        ),
                    )
        return tuple(violations)


class ResultDTOClassesLiveUnderScopeDTOsPackageRule(ArchitectureRuleBase):
    """Require DTO classes to live in the scope `dtos` package.

    Use-case output DTOs are application boundary objects and should not be
    hidden inside use-case modules or other implementation packages.
    """

    id: SpecxRuleId = SpecxRuleId.RESULT_DTO_CLASSES_LIVE_UNDER_SCOPE_DTOS_PACKAGE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            relative_parts = path.relative_to(context.src_root / "core").parts
            if len(relative_parts) < 2:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                nearest_bases = nearest_foundation_base_names_for_class(node.name, base_index)
                is_dto = any(
                    class_suffix_from_base(found_base) == "DTO" for found_base in nearest_bases
                )
                if is_dto and relative_parts[1] != "dtos":
                    violations.append(
                        _violation(self.id, path=path, message="DTO outside dtos", symbol=node.name)
                    )
        return tuple(violations)


class UseCaseInputsAreLocalCommandsOrQueriesRule(ArchitectureRuleBase):
    """Require every use case to accept one same-file command or query input.

    A single local input object makes use-case contracts reviewable, typed, and
    easy for agents to evolve without leaking delivery schemas into core code.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASE_INPUTS_ARE_LOCAL_COMMANDS_OR_QUERIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            local_inputs: dict[str, str] = {}
            use_cases: list[ast.ClassDef] = []
            consumed_inputs: set[str] = set()
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                base_names = class_direct_base_names(node, aliases)
                input_base = next(
                    (
                        found_base
                        for found_base in base_names
                        if found_base in USE_CASE_INPUT_BASE_NAMES
                    ),
                    None,
                )
                if input_base is not None:
                    local_inputs[node.name] = input_base
                if "BaseUseCase" in base_names or class_has_foundation_base(
                    node.name,
                    "BaseUseCase",
                    base_index,
                ):
                    use_cases.append(node)

            for use_case in use_cases:
                execute_methods = [
                    node
                    for node in use_case.body
                    if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
                    and node.name == "execute"
                ]
                if len(execute_methods) != 1:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="missing one execute method",
                            symbol=use_case.name,
                        )
                    )
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
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="execute must accept one keyword-only input",
                            symbol=use_case.name,
                        )
                    )
                    continue
                input_arg = args.kwonlyargs[0]
                input_name = input_arg.arg
                input_annotation = annotation_name(input_arg.annotation, aliases)
                input_base = local_inputs.get(input_annotation)
                if input_name not in USE_CASE_INPUT_ARGUMENTS or input_base is None:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="execute input is not a local command/query",
                            symbol=use_case.name,
                        )
                    )
                    continue
                consumed_inputs.add(input_annotation)
                if input_name == "command" and input_base != "BaseCommand":
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="command input does not inherit BaseCommand",
                            symbol=use_case.name,
                        )
                    )
                if input_name == "query" and input_base != "BaseQuery":
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="query input does not inherit BaseQuery",
                            symbol=use_case.name,
                        )
                    )

            for input_class_name in sorted(set(local_inputs) - consumed_inputs):
                violations.append(
                    _violation(
                        self.id, path=path, message="local input is unused", symbol=input_class_name
                    )
                )
        return tuple(violations)


class CommandAndQueryClassesLiveWithUseCasesRule(ArchitectureRuleBase):
    """Require command and query classes to be defined in use-case modules.

    Commands and queries are use-case input contracts, not shared DTOs or delivery
    schemas, so they should stay beside the use case that consumes them.
    """

    id: SpecxRuleId = SpecxRuleId.COMMAND_AND_QUERY_CLASSES_LIVE_WITH_USE_CASES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            if "use_cases" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ClassDef)
                    and class_direct_base_names(node, aliases) & USE_CASE_INPUT_BASE_NAMES
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="command/query outside use_cases",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class CapabilitiesLiveInExpectedPackagesAndUseExpectedSuffixesRule(ArchitectureRuleBase):
    """Keep capability classes in capability packages with capability naming.

    Capabilities are narrow injectable abilities, so placement and suffix checks
    prevent them from drifting into services, repositories, gateways, or helpers.
    """

    id: SpecxRuleId = SpecxRuleId.CAPABILITIES_LIVE_IN_EXPECTED_PACKAGES_AND_USE_EXPECTED_SUFFIXES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            relative_parts = path.relative_to(context.src_root).parts
            relative_layer = next(iter(relative_parts), "")
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not class_has_foundation_base(node.name, "BaseCapability", base_index):
                    continue
                if relative_layer == "core":
                    inner_package = relative_parts[2] if len(relative_parts) > 2 else ""
                    if inner_package != "capabilities":
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message="capability outside capabilities",
                                symbol=node.name,
                            )
                        )
                elif relative_layer != "shared":
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="capability outside core/shared",
                            symbol=node.name,
                        )
                    )
                if "BaseCapability" in class_direct_base_names(
                    node, aliases
                ) and not node.name.endswith("Capability"):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="direct BaseCapability subclass must end with Capability",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class CapabilitiesDoNotOwnWorkflowsOrOtherPortRolesRule(ArchitectureRuleBase):
    """Prevent capabilities from pretending to be workflows or ports.

    A capability should be small and replaceable; it must not own UoW lifecycle
    or take on repository, gateway, use-case, service, helper, or manager roles.
    """

    id: SpecxRuleId = SpecxRuleId.CAPABILITIES_DO_NOT_OWN_WORKFLOWS_OR_OTHER_PORT_ROLES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                if not class_has_foundation_base(class_node.name, "BaseCapability", base_index):
                    continue
                role_name = class_node.name.removesuffix("Capability")
                forbidden_suffix = next(
                    (
                        suffix
                        for suffix in CAPABILITY_FORBIDDEN_NAME_SUFFIXES
                        if class_node.name.endswith(suffix) or role_name.endswith(suffix)
                    ),
                    None,
                )
                if forbidden_suffix is not None:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"uses {forbidden_suffix} role name",
                            symbol=class_node.name,
                        )
                    )
                for incompatible_base in ("BaseRepository", "BaseGateway", "BaseUseCase"):
                    if class_has_foundation_base(class_node.name, incompatible_base, base_index):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"also inherits {incompatible_base}",
                                symbol=class_node.name,
                            )
                        )
                uow_fields = class_unit_of_work_field_names(class_node, aliases)
                if uow_fields:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"depends on {sorted(uow_fields)}",
                            symbol=class_node.name,
                        )
                    )
                for child in class_node.body:
                    if not isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        continue
                    context_fields = context_self_fields(child, uow_fields)
                    if context_fields:
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"opens {sorted(context_fields)}",
                                symbol=class_node.name,
                            )
                        )
        return tuple(violations)


class GatewayPortsAndImplementationsLiveInExpectedPackagesRule(ArchitectureRuleBase):
    """Keep gateway ports and concrete gateway implementations in distinct packages.

    Gateway ports belong under `gateways`; concrete external-system adapters
    belong under scope infrastructure so the boundary is clear.
    """

    id: SpecxRuleId = SpecxRuleId.GATEWAY_PORTS_AND_IMPLEMENTATIONS_LIVE_IN_EXPECTED_PACKAGES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.core_paths():
            relative_parts = path.relative_to(context.src_root / "core").parts
            if len(relative_parts) < 2:
                continue
            inner_package = relative_parts[1]
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not class_has_foundation_base(node.name, "BaseGateway", base_index):
                    continue
                direct_bases = class_direct_base_names(node, aliases)
                if "BaseGateway" in direct_bases and inner_package != "gateways":
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="gateway port outside gateways",
                            symbol=node.name,
                        )
                    )
                if "BaseGateway" not in direct_bases and inner_package != "infrastructure":
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="gateway implementation outside infrastructure",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class GatewaysDeclareExternalEffectsAndDoNotReturnEntitiesRule(ArchitectureRuleBase):
    """Require gateway ports to document external effects and avoid entity returns.

    Gateways represent outbound business capabilities, so their public contract
    should say what external effect occurs and return DTOs or explicit results.
    """

    id: SpecxRuleId = SpecxRuleId.GATEWAYS_DECLARE_EXTERNAL_EFFECTS_AND_DO_NOT_RETURN_ENTITIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.core_paths():
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not class_has_foundation_base(node.name, "BaseGateway", base_index):
                    continue
                if not declares_external_effect(node):
                    violations.append(
                        _violation(
                            self.id, path=path, message="missing external effect", symbol=node.name
                        )
                    )
                for child in node.body:
                    if not isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        continue
                    return_annotation = annotation_name(child.returns, aliases)
                    if "Entity" in return_annotation:
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"{child.name} returns {return_annotation}",
                                symbol=node.name,
                            )
                        )
        return tuple(violations)


class QueryUseCasesDoNotCallRepositoryMutatorsRule(ArchitectureRuleBase):
    """Keep query use cases read-only by rejecting repository mutator calls.

    Query inputs promise observation rather than state change, so mutating
    repository calls should remain in command use cases.
    """

    id: SpecxRuleId = SpecxRuleId.QUERY_USE_CASES_DO_NOT_CALL_REPOSITORY_MUTATORS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        mutator_names = repository_mutator_method_names(context)
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            local_input_classes = {
                node.name: class_direct_base_names(node, aliases)
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            }
            for class_node, execute in execute_methods_with_classes(tree):
                if len(execute.args.kwonlyargs) != 1 or execute.args.kwonlyargs[0].arg != "query":
                    continue
                query_annotation = annotation_name(execute.args.kwonlyargs[0].annotation, aliases)
                if "BaseQuery" not in local_input_classes.get(query_annotation, set()):
                    continue
                repository_fields = class_injected_repository_field_names(
                    class_node,
                    aliases,
                    base_index,
                )
                repository_roots = active_uow_names(execute) | active_repository_names(
                    execute,
                    self_attribute_names=repository_fields,
                )
                mutator_calls = [
                    call.func.attr
                    for call in ast.walk(execute)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr in mutator_names
                    and (
                        call_is_rooted_in_names(call, repository_roots)
                        or call_is_rooted_in_self_attributes(call, repository_fields)
                    )
                ]
                if mutator_calls:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"calls {sorted(set(mutator_calls))}",
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)


class NonFoundationSourceClassesHaveExplicitBaseClassesRule(ArchitectureRuleBase):
    """Require every non-foundation project class to declare an explicit base.

    Explicit foundation ancestry keeps architecture categories reviewable and
    gives rules a stable way to classify project classes.
    """

    id: SpecxRuleId = SpecxRuleId.NON_FOUNDATION_SOURCE_CLASSES_HAVE_EXPLICIT_BASE_CLASSES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not node.bases:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="class has no explicit base",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class ClassesRequireExampleDocstringsRule(ArchitectureRuleBase):
    """Require project classes to explain their scope with a concrete example.

    Useful docstrings give agents enough context to preserve architectural
    intent without relying on placeholder or ceremony-only comments.
    """

    id: SpecxRuleId = SpecxRuleId.CLASSES_REQUIRE_EXAMPLE_DOCSTRINGS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not has_scoped_example_docstring(node):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="missing scoped Example docstring",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class ServiceClassesUseServiceSuffixRule(ArchitectureRuleBase):
    """Require classes in service packages to use the `Service` suffix.

    The suffix keeps reusable application behavior distinct from capabilities,
    gateways, repositories, controllers, and other class categories.
    """

    id: SpecxRuleId = SpecxRuleId.SERVICE_CLASSES_USE_SERVICE_SUFFIX

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        paths = [
            *(context.src_root / "core").glob("*/services/**/*.py"),
            *(context.src_root / "delivery").glob("**/services/**/*.py"),
        ]
        violations: list[SpecxArchitectureViolation] = []
        for path in paths:
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not node.name.endswith("Service"):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="service class must end with Service",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class CoreServicesUseEffectSpecificServiceBasesRule(ArchitectureRuleBase):
    """Require core services to choose pure, read, or effect service bases.

    The service base communicates whether a service is deterministic, read-only,
    or side-effecting, which makes transaction ownership easier to review.
    """

    id: SpecxRuleId = SpecxRuleId.CORE_SERVICES_USE_EFFECT_SPECIFIC_SERVICE_BASES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.core_service_paths():
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not class_has_any_foundation_base(
                    node.name,
                    CORE_SERVICE_BASE_NAMES,
                    base_index,
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="core service lacks effect-specific base",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class GenericBaseServiceIsNotUsedRule(ArchitectureRuleBase):
    """Reject generic `BaseService` in favor of effect-specific service bases.

    A generic service base hides whether the service is pure, read-only, or
    side-effecting, reducing the value of architecture guardrails.
    """

    id: SpecxRuleId = SpecxRuleId.GENERIC_BASE_SERVICE_IS_NOT_USED

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "BaseService":
                    violations.append(
                        _violation(
                            self.id, path=path, message="defines BaseService", symbol=node.name
                        )
                    )
                if isinstance(node, ast.ImportFrom):
                    imported_names = {alias.name for alias in node.names}
                    if "BaseService" in imported_names:
                        violations.append(
                            _violation(self.id, path=path, message="imports BaseService")
                        )
        return tuple(violations)


class PureServicesDoNotDependOnIOOrRuntimeStateRule(ArchitectureRuleBase):
    """Keep pure services deterministic and independent from IO or runtime state.

    Pure services should be easy to unit test directly and must not depend on
    repositories, gateways, settings, clocks, randomness, or technical libraries.
    """

    id: SpecxRuleId = SpecxRuleId.PURE_SERVICES_DO_NOT_DEPEND_ON_IO_OR_RUNTIME_STATE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.core_service_paths():
            tree = context.tree(path)
            aliases = context.aliases(path)
            pure_services = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
                and class_has_foundation_base(node.name, "BasePureService", base_index)
            ]
            if not pure_services:
                continue
            for module in context.imports(path):
                if module_has_forbidden_parts(
                    module,
                    roots=PURE_SERVICE_FORBIDDEN_IMPORT_ROOTS,
                    parts=PURE_SERVICE_FORBIDDEN_IMPORT_PARTS,
                ):
                    violations.append(_violation(self.id, path=path, message=f"imports {module}"))
            for class_node in pure_services:
                for dependency_name in class_dependency_annotations(class_node, aliases):
                    fragments = forbidden_dependency_fragments(
                        dependency_name,
                        PURE_SERVICE_FORBIDDEN_DEPENDENCY_FRAGMENTS,
                    )
                    if fragments:
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"uses {dependency_name}",
                                symbol=class_node.name,
                            )
                        )
        return tuple(violations)


class ReadServicesDoNotPerformWritesOrOwnTransactionsRule(ArchitectureRuleBase):
    """Keep read services from writing data or owning transactions.

    Read services may compose read operations, but use cases own transaction
    lifecycle and write operations belong in command flows or effect services.
    """

    id: SpecxRuleId = SpecxRuleId.READ_SERVICES_DO_NOT_PERFORM_WRITES_OR_OWN_TRANSACTIONS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        mutator_names = repository_mutator_method_names(context)
        for path in context.core_service_paths():
            tree = context.tree(path)
            aliases = context.aliases(path)
            read_services = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
                and class_has_foundation_base(node.name, "BaseReadService", base_index)
            ]
            for class_node in read_services:
                manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node, aliases
                )
                if manager_fields:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"injects {sorted(manager_fields)}",
                            symbol=class_node.name,
                        )
                    )
                for child in class_node.body:
                    if not isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        continue
                    uow_args = unit_of_work_argument_names(child, aliases)
                    repository_roots = uow_args | active_repository_names(
                        child, root_names=uow_args
                    )
                    for call in (node for node in ast.walk(child) if isinstance(node, ast.Call)):
                        call_method = call.func.attr if isinstance(call.func, ast.Attribute) else ""
                        if calls_forbidden_method(
                            call,
                            READ_SERVICE_FORBIDDEN_CALL_NAMES,
                            READ_SERVICE_FORBIDDEN_CALL_PREFIXES,
                        ):
                            violations.append(
                                _violation(
                                    self.id,
                                    path=path,
                                    message=f"calls {call_method}",
                                    symbol=class_node.name,
                                )
                            )
                        if (
                            isinstance(call.func, ast.Attribute)
                            and call.func.attr in mutator_names
                            and call_is_rooted_in_names(call, repository_roots)
                        ):
                            violations.append(
                                _violation(
                                    self.id,
                                    path=path,
                                    message=f"calls repository mutator {call.func.attr}",
                                    symbol=class_node.name,
                                )
                            )
        return tuple(violations)


class EffectServicesDoNotOwnTransactionsOrImportDeliveryRule(ArchitectureRuleBase):
    """Keep effect services inside use-case-owned transaction boundaries.

    Effect services may coordinate side effects, but they should not open UoWs,
    commit or roll back transactions, return entities, or import delivery code.
    """

    id: SpecxRuleId = SpecxRuleId.EFFECT_SERVICES_DO_NOT_OWN_TRANSACTIONS_OR_IMPORT_DELIVERY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.core_service_paths():
            tree = context.tree(path)
            aliases = context.aliases(path)
            effect_services = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
                and class_has_foundation_base(node.name, "BaseEffectService", base_index)
            ]
            if not effect_services:
                continue
            for module in context.imports(path):
                if module_has_forbidden_parts(
                    module,
                    roots=EFFECT_SERVICE_FORBIDDEN_IMPORT_ROOTS,
                    parts=EFFECT_SERVICE_FORBIDDEN_IMPORT_PARTS,
                ):
                    violations.append(_violation(self.id, path=path, message=f"imports {module}"))
            for class_node in effect_services:
                manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node, aliases
                )
                if manager_fields:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"injects {sorted(manager_fields)}",
                            symbol=class_node.name,
                        )
                    )
                for child in class_node.body:
                    if not isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        continue
                    return_annotation = annotation_name(child.returns, aliases)
                    if "Entity" in return_annotation:
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"returns {return_annotation}",
                                symbol=class_node.name,
                            )
                        )
                    for call in (node for node in ast.walk(child) if isinstance(node, ast.Call)):
                        if isinstance(call.func, ast.Attribute) and call.func.attr in {
                            "commit",
                            "rollback",
                        }:
                            violations.append(
                                _violation(
                                    self.id,
                                    path=path,
                                    message=f"calls {call.func.attr}",
                                    symbol=class_node.name,
                                )
                            )
        return tuple(violations)


class ClassesUseSuffixFromMostSpecificFoundationCategoryRule(ArchitectureRuleBase):
    """Require class names to use the suffix implied by their foundation base.

    Naming from the most-specific foundation category keeps class purpose visible
    and catches accidental use of broad or misleading base classes.
    """

    id: SpecxRuleId = SpecxRuleId.CLASSES_USE_SUFFIX_FROM_MOST_SPECIFIC_FOUNDATION_CATEGORY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        base_index = class_base_name_index(context)
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                foundation_bases = nearest_foundation_base_names_for_class(node.name, base_index)
                suffixes = {
                    suffix
                    for found_base in foundation_bases
                    if (suffix := category_suffix_from_base(found_base, base_index)) is not None
                }
                if not suffixes:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="has no recognized category",
                            symbol=node.name,
                        )
                    )
                    continue
                if not any(node.name.endswith(suffix) for suffix in suffixes):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"expected {sorted(suffixes)}",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class NonFoundationClassesDoNotUseRawCommonBasesRule(ArchitectureRuleBase):
    """Reject raw common framework/base classes outside the foundation layer.

    Project classes should inherit packaged or project-local foundation bases
    instead of raw `ABC`, `BaseModel`, `BaseSettings`, ORM, or built-in
    exception bases.
    """

    id: SpecxRuleId = SpecxRuleId.NON_FOUNDATION_CLASSES_DO_NOT_USE_RAW_COMMON_BASES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        raw_base_names = {
            "ABC",
            "BaseModel",
            "BaseSettings",
            "DeclarativeBase",
            "Enum",
            "Exception",
            "StrEnum",
            "ValueError",
            "object",
        }
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                raw_bases = {base_name(base, aliases) for base in node.bases} & raw_base_names
                if raw_bases:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"uses {sorted(raw_bases)}",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)


class OnlyIOCDeliveryAppAndTestsImportContainerRule(ArchitectureRuleBase):
    """Restrict `diwire.Container` imports to composition and tests.

    Application classes should receive dependencies rather than importing the
    container or resolving collaborators directly. A delivery lifecycle is the
    narrow exception because it owns app shutdown and closes the container.
    """

    id: SpecxRuleId = SpecxRuleId.ONLY_IOC_DELIVERY_APP_AND_TESTS_IMPORT_CONTAINER

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.source_paths():
            if not uses_diwire_container(context.tree(path)):
                continue
            relative = path.relative_to(context.src_root)
            allowed = relative == Path("ioc/container.py") or _is_delivery_composition_module(
                relative
            )
            if not allowed:
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message="imports diwire.Container outside allowed composition modules",
                    )
                )

            aliases = context.aliases(path)
            for class_node in [
                node for node in ast.walk(context.tree(path)) if isinstance(node, ast.ClassDef)
            ]:
                if _class_injects_diwire_container(
                    class_node,
                    aliases,
                ) and not _class_can_inject_container(
                    relative,
                    class_node,
                    base_index,
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="injects diwire.Container outside delivery lifecycle",
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)


class LoggingDoesNotInjectLoggersRule(ArchitectureRuleBase):
    """Keep logger naming local to the class that emits log records.

    Runtime logging is configured once through infrastructure. Classes that log
    should create their own named stdlib logger instead of injecting or
    registering `logging.Logger` through DI.
    """

    id: SpecxRuleId = SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in sorted(context.ast_project.files):
            if path.name == "__init__.py":
                continue

            tree = context.tree(path)
            aliases = context.aliases(path)
            imports = context.imports(path)
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                for child in class_node.body:
                    if not isinstance(child, ast.AnnAssign) or not isinstance(
                        child.target,
                        ast.Name,
                    ):
                        continue
                    if _is_injected_logger_annotation(child.annotation, aliases, imports):
                        annotation = annotation_name(child.annotation, aliases)
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=(f"injects logger field {child.target.id}:{annotation}"),
                                symbol=class_node.name,
                            )
                        )

            for node in [child for child in ast.walk(tree) if isinstance(child, ast.Call)]:
                if not _is_container_registration_call(node):
                    continue
                provides = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "provides"),
                    None,
                )
                if provides is not None and _is_logging_logger_expression(
                    provides,
                    aliases,
                    imports,
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="registers logging.Logger in the DI container",
                        )
                    )
        return tuple(violations)


ALLOWED_UNVERSIONED_OPERATIONAL_ROUTE_PATHS = frozenset({"/healthz", "/readyz"})


class PublicRoutesUseFullAPIV1PathsRule(ArchitectureRuleBase):
    """Require public business route registrations to use full `/api/v1/...` paths.

    Full route paths make public API shape visible at each registration site.
    Operational probe routes are allowed as explicit unversioned exceptions.
    """

    id: SpecxRuleId = SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS
    family = "fastapi"
    default_enabled = False
    required_project_surface: str | None = "delivery/fastapi"

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "delivery").glob("**/controllers/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
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
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="has dynamic route path",
                            node=node,
                        )
                    )
                    continue
                route_path = path_keyword.value.value
                if not isinstance(route_path, str):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"uses {route_path!r}",
                            node=path_keyword.value,
                        )
                    )
                    continue
                if route_path in ALLOWED_UNVERSIONED_OPERATIONAL_ROUTE_PATHS:
                    continue
                if not route_path.startswith("/api/v1/"):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"uses {route_path!r}",
                            node=path_keyword.value,
                        )
                    )
        return tuple(violations)


class NoSchemaBootstrapCallsInSourceOrTestsRule(ArchitectureRuleBase):
    """Reject SQLAlchemy schema bootstrap calls in source and tests.

    SQLAlchemy projects should use Alembic migrations and drift checks instead
    of `metadata.create_all()` or `drop_all()` shortcuts.
    """

    id: SpecxRuleId = SpecxRuleId.NO_SCHEMA_BOOTSTRAP_CALLS_IN_SOURCE_OR_TESTS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for root in (context.src_root, context.project_root / "tests"):
            for path in root.rglob("*.py"):
                if path not in context.ast_project.files:
                    continue
                tree = context.tree(path)
                if any(
                    is_schema_bootstrap_call(node)
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                ):
                    violations.append(
                        _violation(self.id, path=path, message="calls create_all/drop_all")
                    )
        return tuple(violations)


class RootAgentsMDDocumentsProjectCommandsAndBoundariesRule(ArchitectureRuleBase):
    """Keep generated-project agent guidance aligned with commands and boundaries.

    `AGENTS.md` is part of the generated project contract; it must document the
    runnable commands and core Specx rules without drifting from the Makefile.
    """

    id: SpecxRuleId = SpecxRuleId.ROOT_AGENTS_MD_DOCUMENTS_PROJECT_COMMANDS_AND_BOUNDARIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        path = context.project_root / "AGENTS.md"
        if not path.exists():
            return (_violation(self.id, path=path, message="AGENTS.md is missing"),)
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())
        required_fragments = {
            f"Package lives under `src/{context.config.package_name}`",
            "make check",
            "make lint",
            "make test",
            "LoggingConfigurator",
            "Do not inject loggers",
        }
        base_index = class_base_name_index(context)
        optional_base_fragments = {
            "BaseCapability": "BaseCapability",
            "BaseGateway": "BaseGateway",
            "BasePureService": "BasePureService",
            "BaseReadService": "BaseReadService",
            "BaseEffectService": "BaseEffectService",
        }
        required_fragments.update(
            fragment
            for base, fragment in optional_base_fragments.items()
            if _project_uses_foundation_base(base_index, base)
        )
        if _project_uses_foundation_base(base_index, "BaseUseCase"):
            required_fragments.add("Use cases return DTOs, not entities")
        if _project_uses_foundation_base(base_index, "BaseQuery"):
            required_fragments.add("Query use cases must not call repository mutators")
        if _required_integration_test_source_paths(context):
            required_fragments.update(
                {
                    "Use cases that touch persistence inject `UnitOfWorkManager`",
                    "must not inject repositories, active UoWs, providers",
                    "SQLAlchemy sessions/engines/session factories",
                }
            )
        if _project_uses_alembic(context):
            required_fragments.update(
                {
                    "make migration-check",
                    "make makemigrations",
                    "Do not use `create_all()` or `drop_all()`",
                }
            )
        violations: list[SpecxArchitectureViolation] = []
        missing_fragments = sorted(
            fragment
            for fragment in required_fragments
            if " ".join(fragment.split()) not in normalized_text
        )
        if missing_fragments:
            violations.append(
                _violation(self.id, path=path, message=f"missing fragments {missing_fragments}")
            )
        missing_make_targets = sorted(documented_make_targets(text) - context.makefile_targets())
        if missing_make_targets:
            violations.append(
                _violation(
                    self.id,
                    path=path,
                    message=f"documents missing make targets {missing_make_targets}",
                )
            )
        return tuple(violations)


class FastAPIRootAgentsMDDocumentsDeliveryRule(ArchitectureRuleBase):
    """Require FastAPI projects to document their delivery entrypoint and lifecycle.

    Technology-specific delivery guidance is opt-in so framework-neutral
    projects keep the core Specx architecture contract without fake FastAPI paths.
    """

    id: SpecxRuleId = SpecxRuleId.FASTAPI_ROOT_AGENTS_MD_DOCUMENTS_DELIVERY
    family = "fastapi"
    default_enabled = False
    required_project_surface: str | None = "delivery/fastapi"

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        path = context.project_root / "AGENTS.md"
        if not path.exists():
            return (_violation(self.id, path=path, message="AGENTS.md is missing"),)

        normalized_text = " ".join(path.read_text(encoding="utf-8").split())
        required_fragments = {
            f"FastAPI entrypoint: `{context.config.package_name}.delivery.fastapi.__main__:app`",
            "FastAPILifecycle",
            "container.aclose()",
        }
        missing_fragments = sorted(
            fragment
            for fragment in required_fragments
            if " ".join(fragment.split()) not in normalized_text
        )
        if not missing_fragments:
            return ()

        return (_violation(self.id, path=path, message=f"missing fragments {missing_fragments}"),)


class TestsMirrorSourceStructureRule(ArchitectureRuleBase):
    """Require meaningful generated-service tests to mirror source modules.

    The required generated scope is core services, use cases, and capabilities.
    Existing unit and integration tests still need to mirror source modules so
    behavior ownership stays explicit without forcing infrastructure filler.
    """

    id: SpecxRuleId = SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        violations.extend(self._unmapped_test_violations(context))
        violations.extend(self._test_support_structure_violations(context))
        violations.extend(self._missing_required_test_violations(context))
        return tuple(violations)

    def _unmapped_test_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for test_root_name in ("unit", "integration"):
            test_root = context.project_root / "tests" / test_root_name
            if not test_root.exists():
                continue
            for path in _mirrored_test_paths(context, test_root=test_root):
                if _is_non_source_integration_test(path, test_root=test_root):
                    continue
                relative = path.relative_to(test_root)
                if _is_core_behavior_test_path(relative):
                    if path.name.startswith("test_") and _is_core_behavior_target_test_path(
                        relative
                    ):
                        expected_path = test_root / relative.parent.parent / relative.name
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=(
                                    "core behavior test must be flat; expected "
                                    f"{expected_path.relative_to(context.project_root)}"
                                ),
                            )
                        )
                        continue
                    source_paths = _source_paths_for_test_path(
                        path,
                        test_root=test_root,
                        src_root=context.src_root,
                    )
                    if not any(
                        source_path in context.ast_project.files for source_path in source_paths
                    ):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=(
                                    "test does not mirror a source module; expected "
                                    f"{source_paths[0].relative_to(context.project_root)}"
                                ),
                            )
                        )
                    continue
                source_paths = _source_paths_for_test_path(
                    path,
                    test_root=test_root,
                    src_root=context.src_root,
                )
                if not any(
                    source_path in context.ast_project.files for source_path in source_paths
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=(
                                "test does not mirror a source module; expected "
                                f"{source_paths[0].relative_to(context.project_root)}"
                            ),
                        )
                    )
        return tuple(violations)

    def _test_support_structure_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        test_root = context.project_root / "tests"
        support_root = test_root / "_support"
        support_fakes_root = support_root / "fakes"
        if _support_fakes_package_exists(support_fakes_root):
            violations.append(
                _violation(
                    self.id,
                    path=support_fakes_root,
                    message=(
                        "tests/_support/fakes is not allowed; keep one-off doubles in test "
                        "modules and reused unit doubles in mirrored fake_<source_module>.py "
                        "modules"
                    ),
                )
            )
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(test_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            if path.name == "harness.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "harness.py is not allowed; resolve targets directly from the "
                            "container in flat test modules"
                        ),
                    )
                )
            if path.name == "_fakes.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "shared _fakes.py files are not allowed; use mirrored "
                            "fake_<source_module>.py modules for reused unit doubles"
                        ),
                    )
                )
            if _is_fake_module_path(path) and not _is_allowed_mirrored_fake_module_path(
                path,
                test_root=test_root,
            ):
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "fake_*.py modules are allowed only under tests/unit/core "
                            "capabilities, gateways, or repositories packages and must mirror "
                            "a source module"
                        ),
                    )
                )
            if path.name == "conftest.py":
                for class_node in [
                    node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                ]:
                    if not _is_test_double_class_name(class_node.name):
                        continue
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=class_node.name,
                            message=(
                                "test double classes do not belong in conftest.py; define "
                                "them in the test module that uses them"
                            ),
                        )
                    )
            if path.name == "_scenarios.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "generic scenario files are not allowed; keep setup in the "
                            "test module that uses it"
                        ),
                    )
                )
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_pytest_fixture(node, aliases):
                    continue
                if _fixture_returns_use_closure(node):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=(
                                "closure-style use_* fixture factories are not allowed; "
                                "register overrides directly before container.resolve(...)"
                            ),
                        )
                    )
            if not path.is_relative_to(support_root):
                continue
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                if not _is_target_specific_test_factory_or_harness(class_node.name):
                    continue
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        symbol=class_node.name,
                        message=(
                            "target-specific test factories and harnesses are not allowed; "
                            "resolve targets directly from the container"
                        ),
                    )
                )
        return tuple(violations)

    def _missing_required_test_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for source_path in _required_unit_test_source_paths(context):
            flat_path = _flat_test_path_for_source_path(
                source_path,
                test_root=context.project_root / "tests" / "unit",
                src_root=context.src_root,
            )
            if flat_path in context.ast_project.files or _target_folder_test_exists(
                flat_path,
                context=context,
            ):
                continue
            violations.append(
                _violation(
                    self.id,
                    path=source_path,
                    message=f"missing unit test {flat_path.relative_to(context.project_root)}",
                )
            )
        for source_path in _required_integration_test_source_paths(context):
            expected_path = _flat_test_path_for_source_path(
                source_path,
                test_root=context.project_root / "tests" / "integration",
                src_root=context.src_root,
            )
            if expected_path in context.ast_project.files or _target_folder_test_exists(
                expected_path,
                context=context,
            ):
                continue
            violations.append(
                _violation(
                    self.id,
                    path=source_path,
                    message=(
                        "missing integration test "
                        f"{expected_path.relative_to(context.project_root)}"
                    ),
                )
            )
        return tuple(violations)


def _target_folder_test_exists(
    flat_path: Path,
    *,
    context: ArchitectureContext,
) -> bool:
    target_name = flat_path.stem.removeprefix("test_")
    target_folder_path = flat_path.parent / target_name / flat_path.name

    return target_folder_path in context.ast_project.files


class TestFixturesDoNotBundleMocksRule(ArchitectureRuleBase):
    """Reject grouped mock fixtures in generated-service tests.

    A mock fixture should override one collaborator for the behavior under
    test. Class-keyed dictionaries of unrelated mocks make tests unclear about
    what is mocked and what behavior is actually under assertion.
    """

    id: SpecxRuleId = SpecxRuleId.TEST_FIXTURES_DO_NOT_BUNDLE_MOCKS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        test_root = context.project_root / "tests"
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(test_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_pytest_fixture(node, aliases):
                    continue
                if _fixture_bundles_mocks(node, aliases):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=("bundles multiple mocks; use one fixture per collaborator"),
                        )
                    )
        return tuple(violations)


class IntegrationTestsDoNotMockInternalCollaboratorsRule(ArchitectureRuleBase):
    """Require integration tests to exercise the real internal application graph.

    Integration tests may stub external systems, but internal use cases,
    services, and capabilities should be resolved through the real container so
    delivery, DI, transaction, and persistence behavior are covered together.
    """

    id: SpecxRuleId = SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        integration_root = context.project_root / "tests" / "integration"
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(integration_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            imports = context.imports(path)
            factory_return_annotations = _local_function_return_annotations(tree, aliases)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if _function_mocks_internal_app_collaborator(
                    node,
                    aliases,
                    imports,
                    context.config.package_name,
                    factory_return_annotations,
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=(
                                "mocks internal use case, service, or capability in "
                                "integration tests; use the real app graph"
                            ),
                        )
                    )
        return tuple(violations)


class ServicesDoNotOpenUnitOfWorkScopesRule(ArchitectureRuleBase):
    """Reject service-owned unit-of-work scopes.

    Use cases own transaction lifecycle; services may receive active UoWs as
    method arguments but should not open manager contexts themselves.
    """

    id: SpecxRuleId = SpecxRuleId.SERVICES_DO_NOT_OPEN_UNIT_OF_WORK_SCOPES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/services/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                uow_fields = class_unit_of_work_field_names(class_node, aliases)
                if not uow_fields:
                    continue
                for child in class_node.body:
                    if not isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        continue
                    context_fields = context_self_fields(child, uow_fields)
                    if context_fields:
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=f"opens {sorted(context_fields)}",
                                symbol=class_node.name,
                            )
                        )
        return tuple(violations)


class UseCasesOpenAtMostOneUnitOfWorkScopeRule(ArchitectureRuleBase):
    """Limit each use-case execution to one unit-of-work manager scope.

    Repeated transaction scopes in one use-case make lifecycle and rollback
    behavior hard to reason about.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_OPEN_AT_MOST_ONE_UNIT_OF_WORK_SCOPE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for class_node, execute in execute_methods_with_classes(tree):
                manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node,
                    aliases,
                )
                count = uow_manager_context_count(execute, manager_fields)
                if count > 1:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"opens {count} UoWs",
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)


class UseCasesInjectUnitOfWorkManagersRule(ArchitectureRuleBase):
    """Require persistence use cases to inject managers, not active UoWs or providers.

    A use case should receive an injected `*UnitOfWorkManager` and open the
    active unit of work inside `execute(...)`.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_INJECT_UNIT_OF_WORK_MANAGERS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                base_names = class_direct_base_names(class_node, aliases)
                if "BaseUseCase" not in base_names and not class_has_foundation_base(
                    class_node.name,
                    "BaseUseCase",
                    base_index,
                ):
                    continue
                injected_manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node,
                    aliases,
                )
                bad_dependency_fields: list[str] = []
                for child in class_node.body:
                    if not isinstance(child, ast.AnnAssign):
                        continue
                    annotation = annotation_name(child.annotation, aliases)
                    injected_name = injected_type_name(child.annotation, aliases)
                    field_name = child.target.id if isinstance(child.target, ast.Name) else ""
                    if "Provider" in annotation:
                        bad_dependency_fields.append(f"{field_name}:{annotation}")
                    if "UnitOfWork" in annotation and "UnitOfWorkManager" not in annotation:
                        bad_dependency_fields.append(f"{field_name}:{annotation}")
                    if "UnitOfWorkManager" in annotation:
                        if injected_name.endswith("UnitOfWorkManager"):
                            continue
                        bad_dependency_fields.append(f"{field_name}:{annotation}")
                for child in class_node.body:
                    if (
                        isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef))
                        and child.name == "execute"
                    ):
                        context_fields = uow_manager_context_fields(child, injected_manager_fields)
                        unknown_context_fields = context_fields - injected_manager_fields
                        if unknown_context_fields:
                            bad_dependency_fields.append(
                                "opens non-injected manager fields "
                                f"{sorted(unknown_context_fields)}",
                            )
                        if injected_manager_fields and not context_fields:
                            bad_dependency_fields.append("injects UoW manager but does not open it")
                if bad_dependency_fields:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=str(bad_dependency_fields),
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)


class UseCasesDoNotInjectRepositoriesOrInfrastructureRule(ArchitectureRuleBase):
    """Require persistence access to flow through use-case-owned UoW scopes.

    Use cases should inject services and UoW managers, not repositories,
    SQLAlchemy resources, or concrete infrastructure adapters that bypass
    transaction ownership.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue

            tree = context.tree(path)
            aliases = context.aliases(path)
            for module in sorted(context.imports(path)):
                if _use_case_imports_persistence_infrastructure(module):
                    violations.append(_violation(self.id, path=path, message=f"imports {module}"))

            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                if not _is_use_case_class(class_node, aliases, base_index):
                    continue

                messages: list[str] = []
                forbidden_fields = _forbidden_use_case_persistence_dependency_fields(
                    class_node,
                    aliases,
                    base_index,
                )
                if forbidden_fields:
                    messages.append(f"injects {forbidden_fields}")

                manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node,
                    aliases,
                )
                repository_fields = class_injected_repository_field_names(
                    class_node,
                    aliases,
                    base_index,
                )
                for child in class_node.body:
                    if (
                        isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef))
                        and child.name == "execute"
                    ):
                        bad_calls = _repository_calls_outside_manager_owned_uow(
                            child,
                            manager_fields=manager_fields,
                            repository_fields=repository_fields,
                        )
                        if bad_calls:
                            messages.append(
                                f"calls repositories outside manager-owned UoW {sorted(bad_calls)}",
                            )

                if messages:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="; ".join(messages),
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)


class IOCContainerDoesNotRegisterActiveUnitOfWorkRule(ArchitectureRuleBase):
    """Reject active unit-of-work registrations in the IOC container.

    Containers should register managers or factories, not active transaction
    objects whose lifecycle belongs inside a use-case execution.
    """

    id: SpecxRuleId = SpecxRuleId.IOC_CONTAINER_DOES_NOT_REGISTER_ACTIVE_UNIT_OF_WORK

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        path = context.src_root / "ioc" / "container.py"
        if path not in context.ast_project.files:
            return ()
        tree = context.tree(path)
        aliases = context.aliases(path)
        violations: list[SpecxArchitectureViolation] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "diwire"
                and any(
                    aliases.get(alias.asname or alias.name, alias.name) == "Lifetime"
                    for alias in node.names
                )
            ):
                violations.append(_violation(self.id, path=path, message="imports Lifetime"))
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "add":
                continue
            provides = next(
                (keyword.value for keyword in node.keywords if keyword.arg == "provides"), None
            )
            provides_name = annotation_name(provides, aliases)
            if provides_name.endswith("UnitOfWork") and not provides_name.endswith(
                "UnitOfWorkManager"
            ):
                violations.append(
                    _violation(self.id, path=path, message=f"registers active {provides_name}")
                )
        return tuple(violations)


class InitFilesAreEmptyRule(ArchitectureRuleBase):
    """Require package `__init__.py` files to stay empty.

    Empty initializers avoid hidden imports, re-exports, import cycles, and
    package-level behavior that makes agent edits harder to reason about.
    """

    id: SpecxRuleId = SpecxRuleId.INIT_FILES_ARE_EMPTY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for package_root in (context.src_root, context.project_root / "tests"):
            if not package_root.exists():
                continue
            for directory in _python_package_directories(context, root=package_root):
                init_path = directory / "__init__.py"
                if not init_path.exists():
                    violations.append(
                        _violation(self.id, path=init_path, message="__init__.py is missing")
                    )
                    continue
                if init_path.read_text(encoding="utf-8") != "":
                    violations.append(
                        _violation(self.id, path=init_path, message="__init__.py is not empty")
                    )
        return tuple(violations)


def _python_package_directories(
    context: ArchitectureContext,
    *,
    root: Path,
) -> tuple[Path, ...]:
    directories: set[Path] = set()
    for path in context.ast_project.files:
        if not path.is_relative_to(root):
            continue
        parent = path.parent
        while parent.is_relative_to(root):
            directories.add(parent)
            if parent == root:
                break
            parent = parent.parent
    return tuple(sorted(directories))


def _is_use_case_class(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
    class_base_name_index: dict[str, set[str]],
) -> bool:
    base_names = class_direct_base_names(class_node, aliases)
    return "BaseUseCase" in base_names or class_has_foundation_base(
        class_node.name,
        "BaseUseCase",
        class_base_name_index,
    )


def _use_case_imports_persistence_infrastructure(module: str) -> bool:
    parts = module_parts(module)
    return "infrastructure" in parts or bool(parts and parts[0] == "sqlalchemy")


def _is_scope_technical_import(module: str) -> bool:
    parts = module_parts(module)
    if "core" not in parts:
        return False

    core_index = parts.index("core")
    scope_relative_parts = parts[core_index + 2 :]
    return any(
        part in {"alembic", "infrastructure", "migrations", "models", "repositories"}
        for part in scope_relative_parts
    )


def _forbidden_use_case_persistence_dependency_fields(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
    class_base_name_index: dict[str, set[str]],
) -> list[str]:
    fields: list[str] = []
    for child in class_node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
            continue

        injected_name = injected_type_name(child.annotation, aliases)
        if not injected_name:
            continue

        if _is_forbidden_use_case_persistence_dependency(
            injected_name,
            class_base_name_index,
        ):
            annotation = annotation_name(child.annotation, aliases)
            fields.append(f"{child.target.id}:{annotation}")
    return sorted(fields)


def _is_forbidden_use_case_persistence_dependency(
    dependency_name: str,
    class_base_name_index: dict[str, set[str]],
) -> bool:
    if dependency_name.endswith("Repository") or class_has_foundation_base(
        dependency_name,
        "BaseRepository",
        class_base_name_index,
    ):
        return True

    return any(
        forbidden_name in dependency_name
        for forbidden_name in USE_CASE_FORBIDDEN_INFRASTRUCTURE_DEPENDENCY_NAMES
    )


def _repository_calls_outside_manager_owned_uow(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    *,
    manager_fields: set[str],
    repository_fields: set[str],
) -> set[str]:
    manager_owned_uow_names = active_uow_names_from_manager_fields(function, manager_fields)
    uow_like_names = {
        name for name in active_uow_names(function) if _name_looks_like_unit_of_work(name)
    }
    repository_alias_names = _repository_alias_names_from_uow_names(
        function,
        manager_owned_uow_names | uow_like_names,
    )
    bad_calls: set[str] = set()
    for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
        chain = attribute_chain(call.func)
        if not chain:
            continue
        if chain[0] in manager_owned_uow_names:
            continue
        if chain[0] in uow_like_names and len(chain) >= 3:
            bad_calls.add(".".join(chain))
            continue
        if _call_chain_uses_direct_repository(
            chain,
            repository_fields=repository_fields,
            repository_alias_names=repository_alias_names,
        ):
            bad_calls.add(".".join(chain))
    return bad_calls


def _repository_alias_names_from_uow_names(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    uow_names: set[str],
) -> set[str]:
    aliases: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        value_chain = attribute_chain(node.value)
        if len(value_chain) < 2 or value_chain[0] not in uow_names:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                aliases.add(target.id)
    return aliases


def _call_chain_uses_direct_repository(
    chain: tuple[str, ...],
    *,
    repository_fields: set[str],
    repository_alias_names: set[str],
) -> bool:
    if len(chain) < 2:
        return False
    if chain[0] in repository_alias_names:
        return True
    if chain[0] == "self" and len(chain) >= 3 and chain[1] in repository_fields:
        return True
    return any(_name_looks_like_repository(segment) for segment in chain[:-1])


def _name_looks_like_repository(name: str) -> bool:
    normalized = name.strip("_").lower()
    return normalized == "repository" or normalized.endswith("_repository")


def _name_looks_like_unit_of_work(name: str) -> bool:
    normalized = name.strip("_").lower()
    return normalized in {"unit_of_work", "uow"} or normalized.endswith("_unit_of_work")


def _is_injected_logger_annotation(
    annotation: ast.expr | None,
    aliases: dict[str, str],
    imports: frozenset[str],
) -> bool:
    if annotation is None:
        return False
    if not isinstance(annotation, ast.Subscript):
        return False
    if not annotation_name(annotation.value, aliases).endswith("Injected"):
        return False

    return _is_logging_logger_expression(annotation.slice, aliases, imports)


def _is_injected_container_annotation(
    annotation: ast.expr | None,
    aliases: dict[str, str],
) -> bool:
    if annotation is None:
        return False
    if not isinstance(annotation, ast.Subscript):
        return False
    if not annotation_name(annotation.value, aliases).endswith("Injected"):
        return False

    return _is_diwire_container_expression(annotation.slice, aliases)


def _class_injects_diwire_container(
    class_node: ast.ClassDef,
    aliases: dict[str, str],
) -> bool:
    for child in class_node.body:
        if isinstance(child, ast.AnnAssign) and _is_injected_container_annotation(
            child.annotation,
            aliases,
        ):
            return True
        if isinstance(child, ast.FunctionDef) and child.name == "__init__":
            for argument in (
                *child.args.posonlyargs,
                *child.args.args,
                *child.args.kwonlyargs,
            ):
                if argument.arg == "self":
                    continue
                if _is_injected_container_annotation(argument.annotation, aliases):
                    return True

    return False


def _class_can_inject_container(
    relative: Path,
    class_node: ast.ClassDef,
    class_base_name_index: dict[str, set[str]],
) -> bool:
    return (
        len(relative.parts) == 3
        and relative.parts[0] == "delivery"
        and relative.name == "lifecycle.py"
        and class_node.name.endswith("Lifecycle")
        and class_has_foundation_base(class_node.name, "BaseLifecycle", class_base_name_index)
    )


def _is_delivery_composition_module(relative: Path) -> bool:
    return (
        len(relative.parts) == 3
        and relative.parts[0] == "delivery"
        and relative.name in {"__main__.py", "factory.py", "lifecycle.py"}
    )


def _is_diwire_container_expression(
    expression: ast.expr,
    aliases: dict[str, str],
) -> bool:
    if isinstance(expression, ast.Attribute) and expression.attr == "Container":
        chain = attribute_chain(expression)
        if len(chain) >= 2:
            root_alias = aliases.get(chain[0], chain[0])
            return root_alias == "diwire"

    if isinstance(expression, ast.Name):
        return aliases.get(expression.id, expression.id) == "Container"

    return False


def _is_logging_logger_expression(
    expression: ast.expr,
    aliases: dict[str, str],
    imports: frozenset[str],
) -> bool:
    if isinstance(expression, ast.Attribute) and expression.attr == "Logger":
        chain = attribute_chain(expression)
        if len(chain) >= 2:
            root_alias = aliases.get(chain[0], chain[0])
            return root_alias == "logging"

    if isinstance(expression, ast.Name):
        return aliases.get(expression.id, expression.id) == "Logger" and "logging.Logger" in imports

    return False


def _is_container_registration_call(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and node.func.attr in {
        "add",
        "add_context_manager",
        "add_context_manager_class",
        "add_factory",
        "add_factory_class",
        "add_generator",
        "add_generator_class",
        "add_instance",
    }


def _project_uses_alembic(context: ArchitectureContext) -> bool:
    return (context.project_root / "alembic.ini").exists() or (
        context.project_root / "migrations"
    ).exists()


def _project_uses_foundation_base(
    class_base_names: dict[str, set[str]],
    foundation_base: str,
) -> bool:
    return any(
        class_has_foundation_base(class_name, foundation_base, class_base_names)
        for class_name in class_base_names
    )


def _mirrored_test_paths(
    context: ArchitectureContext,
    *,
    test_root: Path,
) -> tuple[Path, ...]:
    return tuple(
        path
        for path in sorted(context.ast_project.files)
        if path.is_relative_to(test_root)
        and (path.name.startswith("test_") or path.name.startswith("fake_"))
        and path.name.endswith(".py")
    )


def _source_paths_for_test_path(
    path: Path,
    *,
    test_root: Path,
    src_root: Path,
) -> tuple[Path, ...]:
    relative = path.relative_to(test_root)
    source_file_name = relative.name.removeprefix("test_").removeprefix("fake_")
    direct_mirror_path = src_root / relative.parent / source_file_name

    return (direct_mirror_path,)


def _is_fake_module_path(path: Path) -> bool:
    return path.name.startswith("fake_") and path.name.endswith(".py")


def _is_allowed_mirrored_fake_module_path(path: Path, *, test_root: Path) -> bool:
    allowed_fake_package_names = {"capabilities", "gateways", "repositories"}
    unit_core_root = test_root / "unit" / "core"
    if not path.is_relative_to(unit_core_root):
        return False
    relative = path.relative_to(unit_core_root)

    return len(relative.parts) >= 3 and relative.parts[1] in allowed_fake_package_names


def _is_core_behavior_test_path(relative: Path) -> bool:
    parts = relative.parts
    return len(parts) >= 4 and parts[0] == "core" and parts[2] in CORE_BEHAVIOR_TEST_PACKAGE_NAMES


def _is_core_behavior_target_test_path(relative: Path) -> bool:
    source_file_name = relative.name.removeprefix("test_")
    source_stem = Path(source_file_name).stem
    return len(relative.parts) >= 5 and relative.parent.name == source_stem


def _flat_test_path_for_source_path(
    path: Path,
    *,
    test_root: Path,
    src_root: Path,
) -> Path:
    relative = path.relative_to(src_root)
    return test_root / relative.parent / f"test_{relative.name}"


def _is_target_specific_test_factory_or_harness(class_name: str) -> bool:
    return class_name.endswith(
        (
            "CapabilityFactory",
            "CapabilityHarness",
            "ControllerFactory",
            "ControllerHarness",
            "ServiceFactory",
            "ServiceHarness",
            "UseCaseFactory",
            "UseCaseHarness",
        )
    )


def _is_test_double_class_name(class_name: str) -> bool:
    normalized = class_name.lower()
    return (
        normalized.startswith(
            (
                "fake",
                "stub",
                "spy",
                "inmemory",
                "sequenced",
                "fixed",
                "tracking",
                "recording",
                "failing",
                "broken",
            )
        )
        or normalized.endswith(("fake", "stub", "spy", "double", "helper"))
        or "fake" in normalized
        or "double" in normalized
        or "unavailable" in normalized
    )


def _support_fakes_package_exists(path: Path) -> bool:
    return path.exists()


def _is_non_source_integration_test(path: Path, *, test_root: Path) -> bool:
    relative = path.relative_to(test_root)
    return relative.parts[:1] == ("migrations",)


def _required_unit_test_source_paths(context: ArchitectureContext) -> tuple[Path, ...]:
    core_root = context.src_root / "core"
    required_package_names = {"capabilities", "services", "use_cases"}
    return tuple(
        path
        for path in sorted(context.ast_project.files)
        if path.is_relative_to(core_root)
        and path.name != "__init__.py"
        and len((relative := path.relative_to(core_root)).parts) >= 3
        and relative.parts[1] in required_package_names
    )


def _required_integration_test_source_paths(context: ArchitectureContext) -> tuple[Path, ...]:
    base_index = class_base_name_index(context)
    core_root = context.src_root / "core"
    return tuple(
        path
        for path in sorted(context.ast_project.files)
        if path.name != "__init__.py"
        and path.is_relative_to(core_root)
        and len((relative := path.relative_to(core_root)).parts) >= 3
        and relative.parts[1] == "use_cases"
        and _module_has_persistence_use_case(context, path, base_index)
    )


def _module_has_persistence_use_case(
    context: ArchitectureContext,
    path: Path,
    base_index: dict[str, set[str]],
) -> bool:
    tree = context.tree(path)
    aliases = context.aliases(path)
    return any(
        _is_use_case_class(class_node, aliases, base_index)
        and bool(class_injected_unit_of_work_manager_field_names(class_node, aliases))
        for class_node in ast.walk(tree)
        if isinstance(class_node, ast.ClassDef)
    )


def _is_pytest_fixture(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> bool:
    for decorator in node.decorator_list:
        expression = decorator.func if isinstance(decorator, ast.Call) else decorator
        if annotation_name(expression, aliases) == "fixture":
            return True
    return False


def _fixture_returns_use_closure(node: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    inner_use_functions = {
        child.name
        for child in node.body
        if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef))
        and child.name.startswith("use_")
    }
    if not inner_use_functions:
        return False
    return any(
        isinstance(child, ast.Return)
        and isinstance(child.value, ast.Name)
        and child.value.id in inner_use_functions
        for child in node.body
    )


def _function_mocks_internal_app_collaborator(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
    factory_return_annotations: dict[str, str],
) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if _mock_call_uses_internal_app_collaborator_spec(
                child,
                aliases,
                imports,
                package_name,
            ):
                return True
            if _registration_call_targets_internal_app_collaborator(
                child,
                aliases,
                imports,
                package_name,
                factory_return_annotations,
            ):
                return True
            if _patch_call_targets_internal_app_collaborator(
                child,
                aliases,
                imports,
                package_name,
            ):
                return True
            if _monkeypatch_call_targets_internal_app_collaborator(
                child,
                aliases,
                imports,
                package_name,
            ):
                return True
    return False


def _mock_call_uses_internal_app_collaborator_spec(
    node: ast.Call,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
) -> bool:
    if not _is_mock_factory_call(node, aliases):
        return False
    spec_name = _mock_call_spec_name(node, aliases)
    return _is_internal_app_collaborator_name(
        spec_name,
        aliases=aliases,
        imports=imports,
        package_name=package_name,
    )


def _mock_call_spec_name(node: ast.Call, aliases: dict[str, str]) -> str:
    for keyword in node.keywords:
        if keyword.arg in {"spec", "spec_set"}:
            return _qualified_expression_name(keyword.value, aliases)
    if node.args:
        return _qualified_expression_name(node.args[0], aliases)
    return ""


def _registration_call_targets_internal_app_collaborator(
    node: ast.Call,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
    factory_return_annotations: dict[str, str],
) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in {"add", "add_factory", "add_instance", "override"}:
        return False
    provides = next((keyword.value for keyword in node.keywords if keyword.arg == "provides"), None)
    if _is_internal_app_collaborator_name(
        _qualified_expression_name(provides, aliases),
        aliases=aliases,
        imports=imports,
        package_name=package_name,
    ):
        return True
    if node.func.attr in {"add", "add_factory"} and node.args:
        registered_name = _qualified_expression_name(node.args[0], aliases)
        if _is_internal_app_collaborator_name(
            registered_name,
            aliases=aliases,
            imports=imports,
            package_name=package_name,
        ):
            return True
        if isinstance(node.args[0], ast.Name) and _is_internal_app_collaborator_name(
            factory_return_annotations.get(node.args[0].id, ""),
            aliases=aliases,
            imports=imports,
            package_name=package_name,
        ):
            return True
    if node.func.attr in {"add_instance", "override"} and node.args:
        instance = node.args[0]
        if isinstance(instance, ast.Call):
            return _is_internal_app_collaborator_name(
                _qualified_expression_name(instance.func, aliases),
                aliases=aliases,
                imports=imports,
                package_name=package_name,
            )
    return False


def _patch_call_targets_internal_app_collaborator(
    node: ast.Call,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
) -> bool:
    call_chain = tuple(aliases.get(segment, segment) for segment in attribute_chain(node.func))
    if not _is_patch_call_chain(call_chain):
        return False
    if _is_patch_object_call_chain(call_chain):
        if not node.args:
            return False
        return _is_internal_app_collaborator_name(
            _qualified_expression_name(node.args[0], aliases),
            aliases=aliases,
            imports=imports,
            package_name=package_name,
        )
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return False
    return _string_target_names_internal_app_collaborator(
        node.args[0].value,
        package_name=package_name,
    )


def _monkeypatch_call_targets_internal_app_collaborator(
    node: ast.Call,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
) -> bool:
    call_chain = tuple(aliases.get(segment, segment) for segment in attribute_chain(node.func))
    if call_chain[-1:] != ("setattr",) or not node.args:
        return False
    target = node.args[0]
    if isinstance(target, ast.Constant) and _string_target_names_internal_app_collaborator(
        target.value,
        package_name=package_name,
    ):
        return True
    return _is_internal_app_collaborator_name(
        _qualified_expression_name(target, aliases),
        aliases=aliases,
        imports=imports,
        package_name=package_name,
    )


def _string_target_names_internal_app_collaborator(
    value: object,
    *,
    package_name: str,
) -> bool:
    return (
        isinstance(value, str)
        and value.startswith(f"{package_name}.core.")
        and any(_name_looks_like_internal_app_collaborator(segment) for segment in value.split("."))
    )


def _is_internal_app_collaborator_name(
    name: str,
    *,
    aliases: dict[str, str],
    imports: frozenset[str],
    package_name: str,
) -> bool:
    if not _name_looks_like_internal_app_collaborator(name.rsplit(".", maxsplit=1)[-1]):
        return False
    name_chain = tuple(aliases.get(segment, segment) for segment in name.split("."))
    if len(name_chain) >= 2:
        root = name_chain[0]
        suffix = ".".join(name_chain[1:])
        qualified_name = ".".join(name_chain)
        if qualified_name.startswith(f"{package_name}.core."):
            return True
        return any(
            imported.startswith(f"{package_name}.core.")
            and imported.endswith((f".{root}", f".{suffix}"))
            for imported in imports
        )
    return any(
        imported.startswith(f"{package_name}.core.") and imported.endswith(f".{name}")
        for imported in imports
    )


def _name_looks_like_internal_app_collaborator(name: str) -> bool:
    return name.endswith(("Capability", "Service", "UseCase"))


def _is_patch_call_chain(call_chain: tuple[str, ...]) -> bool:
    return call_chain[-1:] == ("patch",) or _is_patch_object_call_chain(call_chain)


def _is_patch_object_call_chain(call_chain: tuple[str, ...]) -> bool:
    return call_chain[-2:] == ("patch", "object")


def _local_function_return_annotations(
    tree: ast.Module,
    aliases: dict[str, str],
) -> dict[str, str]:
    return {
        node.name: annotation_name(node.returns, aliases)
        for node in ast.walk(tree)
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.returns is not None
    }


def _qualified_expression_name(
    expression: ast.expr | None,
    aliases: dict[str, str],
) -> str:
    chain = attribute_chain(expression)
    if chain:
        return ".".join(aliases.get(segment, segment) for segment in chain)
    return annotation_name(expression, aliases)


def _explicit_import_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return tuple(modules)


def _fixture_bundles_mocks(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> bool:
    mock_names = _fixture_mock_assignment_names(node, aliases)
    if _fixture_returns_mock_dict(node, aliases):
        return True
    if _returns_literal_with_multiple_mock_calls(node, aliases):
        return True
    if node.name.endswith("_mocks") and _function_mock_call_count(node, aliases) > 1:
        return True
    if len(mock_names) <= 1:
        return False
    if node.name.endswith("_mocks"):
        return True
    if _returns_dict_of_names(node, mock_names):
        return True
    return _container_add_instance_call_count(node) > 1


def _fixture_returns_mock_dict(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> bool:
    return_annotation = annotation_name(node.returns, aliases)
    return return_annotation.startswith("dict[") and "Mock" in return_annotation


def _fixture_mock_assignment_names(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> set[str]:
    mock_names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign) and _is_mock_factory_call(child.value, aliases):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    mock_names.add(target.id)
        elif (
            isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Name)
            and _is_mock_factory_call(child.value, aliases)
        ):
            mock_names.add(child.target.id)
    return mock_names


def _is_mock_factory_call(expression: ast.expr | None, aliases: dict[str, str]) -> bool:
    if not isinstance(expression, ast.Call):
        return False
    return annotation_name(expression.func, aliases) in {
        "AsyncMock",
        "MagicMock",
        "Mock",
        "create_autospec",
    }


def _returns_dict_of_names(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    names: set[str],
) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Return) or not isinstance(child.value, ast.Dict):
            continue
        if any(isinstance(value, ast.Name) and value.id in names for value in child.value.values):
            return True
    return False


def _returns_literal_with_multiple_mock_calls(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Return):
            continue
        values = _literal_values(child.value)
        if sum(1 for value in values if _is_mock_factory_call(value, aliases)) > 1:
            return True
    return False


def _literal_values(expression: ast.expr | None) -> tuple[ast.expr | None, ...]:
    if isinstance(expression, ast.Dict):
        return tuple(expression.values)
    if isinstance(expression, (ast.List, ast.Set, ast.Tuple)):
        return tuple(expression.elts)
    return ()


def _function_mock_call_count(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    aliases: dict[str, str],
) -> int:
    return sum(
        1
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and _is_mock_factory_call(child, aliases)
    )


def _container_add_instance_call_count(node: ast.AsyncFunctionDef | ast.FunctionDef) -> int:
    return sum(
        1
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == "add_instance"
    )


BUILT_IN_RULES: tuple[type[ArchitectureRuleBase], ...] = (
    CoreInnerPackagesDoNotImportOuterLayersOrIOLibrariesRule,
    ScopeInfrastructureDoesNotImportDeliveryRule,
    DeliveryControllersDoNotImportInfrastructureRule,
    CoreDoesNotContainDeliveryPackagesRule,
    FoundationImportsUseScopedPackagesRule,
    UseCasesDoNotImportOrReturnEntitiesRule,
    UseCasesReturnDTOsRule,
    ResultDTOClassesLiveUnderScopeDTOsPackageRule,
    UseCaseInputsAreLocalCommandsOrQueriesRule,
    CommandAndQueryClassesLiveWithUseCasesRule,
    CapabilitiesLiveInExpectedPackagesAndUseExpectedSuffixesRule,
    CapabilitiesDoNotOwnWorkflowsOrOtherPortRolesRule,
    GatewayPortsAndImplementationsLiveInExpectedPackagesRule,
    GatewaysDeclareExternalEffectsAndDoNotReturnEntitiesRule,
    QueryUseCasesDoNotCallRepositoryMutatorsRule,
    NonFoundationSourceClassesHaveExplicitBaseClassesRule,
    ClassesRequireExampleDocstringsRule,
    ServiceClassesUseServiceSuffixRule,
    CoreServicesUseEffectSpecificServiceBasesRule,
    GenericBaseServiceIsNotUsedRule,
    PureServicesDoNotDependOnIOOrRuntimeStateRule,
    ReadServicesDoNotPerformWritesOrOwnTransactionsRule,
    EffectServicesDoNotOwnTransactionsOrImportDeliveryRule,
    ClassesUseSuffixFromMostSpecificFoundationCategoryRule,
    NonFoundationClassesDoNotUseRawCommonBasesRule,
    OnlyIOCDeliveryAppAndTestsImportContainerRule,
    LoggingDoesNotInjectLoggersRule,
    PublicRoutesUseFullAPIV1PathsRule,
    NoSchemaBootstrapCallsInSourceOrTestsRule,
    RootAgentsMDDocumentsProjectCommandsAndBoundariesRule,
    FastAPIRootAgentsMDDocumentsDeliveryRule,
    TestsMirrorSourceStructureRule,
    TestFixturesDoNotBundleMocksRule,
    IntegrationTestsDoNotMockInternalCollaboratorsRule,
    ServicesDoNotOpenUnitOfWorkScopesRule,
    UseCasesOpenAtMostOneUnitOfWorkScopeRule,
    UseCasesInjectUnitOfWorkManagersRule,
    UseCasesDoNotInjectRepositoriesOrInfrastructureRule,
    IOCContainerDoesNotRegisterActiveUnitOfWorkRule,
    InitFilesAreEmptyRule,
)
