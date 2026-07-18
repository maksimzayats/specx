from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    violation,
)


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
                        violation(
                            self.id,
                            path=path,
                            message="service class must end with Service",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)
