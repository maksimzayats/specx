from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


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
