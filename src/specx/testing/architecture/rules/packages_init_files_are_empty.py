from __future__ import annotations

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _python_package_directories,
    _violation,
)


class InitFilesAreEmptyRule(ArchitectureRuleBase):
    """Require package `__init__.py` files to stay empty.

    Empty initializers avoid hidden imports, re-exports, import cycles, and
    package-level behavior that makes agent edits harder to reason about.
    """

    id: SpecxRuleId = SpecxRuleId.INIT_FILES_ARE_EMPTY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for package_root in (context.src_root, context.project_root / "tests"):
            if not package_root.exists():
                continue
            for directory in _python_package_directories(context, root=package_root):
                init_path = directory / "__init__.py"
                if not init_path.exists():
                    violations.append(
                        _violation(self.id, path=init_path, message="__init__.py is missing")
                    )
                    continue
                if init_path.read_text(encoding="utf-8") != "":
                    violations.append(
                        _violation(self.id, path=init_path, message="__init__.py is not empty")
                    )
        return tuple(violations)
