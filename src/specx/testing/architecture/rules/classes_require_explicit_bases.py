from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


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
