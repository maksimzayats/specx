from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    class_unit_of_work_field_names,
    context_self_fields,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


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
