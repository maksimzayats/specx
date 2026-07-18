from __future__ import annotations

from specx.testing.architecture.context import (
    INNER_PACKAGE_NAMES,
    ArchitectureContext,
    module_parts,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    violation,
)


class CoreInnerPackagesDoNotImportOuterLayersOrIOLibrariesRule(ArchitectureRuleBase):
    """Keep inner core packages free from delivery, infrastructure, IOC, and IO imports.

    This protects core application code from framework and technical dependencies
    that should stay at the delivery, infrastructure, or composition edge.
    """

    id: SpecxRuleId = SpecxRuleId.CORE_INNER_PACKAGES_DO_NOT_IMPORT_OUTER_LAYERS_OR_IO_LIBRARIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/*/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            relative_parts = path.relative_to(context.src_root / "core").parts
            if len(relative_parts) < 2 or relative_parts[1] not in INNER_PACKAGE_NAMES:
                continue
            for module in context.imports(path):
                parts = module_parts(module)
                if "delivery" in parts or "infrastructure" in parts:
                    violations.append(
                        violation(self.id, path=path, message=f"imports {module}"),
                    )
                if "ioc" in parts:
                    violations.append(
                        violation(self.id, path=path, message=f"imports {module}"),
                    )
                if parts and parts[0] in {"fastapi", "httpx", "httpx2", "redis", "sqlalchemy"}:
                    violations.append(
                        violation(self.id, path=path, message=f"imports {module}"),
                    )
        return tuple(violations)
