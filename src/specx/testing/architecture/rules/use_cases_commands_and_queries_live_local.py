from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    USE_CASE_INPUT_BASE_NAMES,
    ArchitectureContext,
    class_definition_base_index,
    class_has_foundation_base_from_path,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    violation,
)


class CommandAndQueryClassesLiveWithUseCasesRule(ArchitectureRuleBase):
    """Require command and query classes to be defined in use-case modules.

    Commands and queries are use-case input contracts, not shared DTOs or delivery
    schemas, so they should stay beside the use case that consumes them.
    """

    id: SpecxRuleId = SpecxRuleId.COMMAND_AND_QUERY_CLASSES_LIVE_WITH_USE_CASES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        definition_index = class_definition_base_index(context)
        for path in (context.src_root / "core").glob("**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            if "use_cases" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and any(
                    class_has_foundation_base_from_path(
                        node.name,
                        base,
                        source_path=path,
                        context=context,
                        definition_index=definition_index,
                    )
                    for base in USE_CASE_INPUT_BASE_NAMES
                ):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            message="command/query outside use_cases",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)
