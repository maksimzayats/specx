from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    annotation_name,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    is_container_registration_call,
    local_function_return_annotations,
    violation,
)


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
        factory_return_annotations = local_function_return_annotations(tree, aliases)
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
                violations.append(violation(self.id, path=path, message="imports Lifetime"))
            if not isinstance(node, ast.Call):
                continue
            if not is_container_registration_call(node):
                continue
            provides = next(
                (keyword.value for keyword in node.keywords if keyword.arg == "provides"), None
            )
            registered_name = _registered_type_name(
                node,
                provides=provides,
                aliases=aliases,
                factory_return_annotations=factory_return_annotations,
            )
            if registered_name.endswith("UnitOfWork") and not registered_name.endswith(
                "UnitOfWorkManager"
            ):
                violations.append(
                    violation(
                        self.id,
                        path=path,
                        message=f"registers active {registered_name}",
                        node=node,
                    )
                )
        return tuple(violations)


def _registered_type_name(
    node: ast.Call,
    *,
    provides: ast.expr | None,
    aliases: dict[str, str],
    factory_return_annotations: dict[str, str],
) -> str:
    if provides is not None:
        return annotation_name(provides, aliases)
    if not node.args:
        return ""

    registered = node.args[0]
    if isinstance(node.func, ast.Attribute) and node.func.attr == "add_instance":
        if isinstance(registered, ast.Call):
            return annotation_name(registered.func, aliases)
        return annotation_name(registered, aliases)
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_factory"
        and isinstance(registered, ast.Name)
    ):
        return factory_return_annotations.get(
            registered.id,
            annotation_name(registered, aliases),
        )
    return annotation_name(registered, aliases)
