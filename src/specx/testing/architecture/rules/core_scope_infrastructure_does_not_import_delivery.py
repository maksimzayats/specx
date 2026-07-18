from __future__ import annotations

from specx.testing.architecture.context import (
    ArchitectureContext,
    module_parts,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    violation,
)


class ScopeInfrastructureDoesNotImportDeliveryRule(ArchitectureRuleBase):
    """Prevent scope infrastructure adapters from depending on delivery code.

    Scope infrastructure can use technical libraries and core contracts, but it
    must not couple adapters back to HTTP controllers, schemas, or app factories.
    """

    id: SpecxRuleId = SpecxRuleId.SCOPE_INFRASTRUCTURE_DOES_NOT_IMPORT_DELIVERY

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "core").glob("*/infrastructure/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            for module in context.imports(path):
                if "delivery" in module_parts(module):
                    violations.append(
                        violation(self.id, path=path, message=f"imports {module}"),
                    )
        return tuple(violations)
