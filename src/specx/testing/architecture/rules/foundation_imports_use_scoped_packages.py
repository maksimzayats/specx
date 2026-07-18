from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    explicit_import_modules,
    violation,
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
                for module in explicit_import_modules(tree):
                    if module == "specx.foundation" or module.startswith("specx.foundation."):
                        violations.append(
                            violation(self.id, path=path, message=f"imports {module}")
                        )
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module == "specx"
                        and any(alias.name == "foundation" for alias in node.names)
                    ):
                        violations.append(
                            violation(
                                self.id,
                                path=path,
                                message="imports specx.foundation",
                                node=node,
                            )
                        )
        return tuple(violations)
