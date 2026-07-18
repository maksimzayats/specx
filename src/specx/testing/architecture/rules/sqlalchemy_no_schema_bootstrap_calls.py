from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    is_schema_bootstrap_call,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    violation,
)


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
                        violation(self.id, path=path, message="calls create_all/drop_all")
                    )
        return tuple(violations)
