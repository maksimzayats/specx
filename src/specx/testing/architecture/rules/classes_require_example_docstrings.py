from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    has_scoped_example_docstring,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


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
