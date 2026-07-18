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
                    violation(self.id, path=path, message=f"registers active {provides_name}")
                )
        return tuple(violations)
