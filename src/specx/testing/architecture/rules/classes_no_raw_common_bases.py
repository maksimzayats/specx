from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    base_name,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


class NonFoundationClassesDoNotUseRawCommonBasesRule(ArchitectureRuleBase):
    """Reject raw common framework/base classes outside the foundation layer.

    Project classes should inherit packaged or project-local foundation bases
    instead of raw `ABC`, `BaseModel`, `BaseSettings`, ORM, or built-in
    exception bases.
    """

    id: SpecxRuleId = SpecxRuleId.NON_FOUNDATION_CLASSES_DO_NOT_USE_RAW_COMMON_BASES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        raw_base_names = {
            "ABC",
            "BaseModel",
            "BaseSettings",
            "DeclarativeBase",
            "Enum",
            "Exception",
            "StrEnum",
            "ValueError",
            "object",
        }
        violations: list[SpecxArchitectureViolation] = []
        for path in context.source_paths():
            if "foundation" in path.relative_to(context.src_root).parts:
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                raw_bases = {base_name(base, aliases) for base in node.bases} & raw_base_names
                if raw_bases:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=f"uses {sorted(raw_bases)}",
                            symbol=node.name,
                        )
                    )
        return tuple(violations)
