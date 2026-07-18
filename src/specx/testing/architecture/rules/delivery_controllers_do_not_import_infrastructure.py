from __future__ import annotations

from specx.testing.architecture.context import (
    ArchitectureContext,
    module_parts,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _explicit_import_modules,
    _is_scope_technical_import,
    _violation,
)


class DeliveryControllersDoNotImportInfrastructureRule(ArchitectureRuleBase):
    """Keep delivery modules from reaching into scope infrastructure.

    Controllers should translate framework input and call use cases; concrete
    infrastructure should be composed through IOC or delivery app factories.
    Delivery app composition modules may import top-level infrastructure
    resources, but not scope repositories, ORM models, DDL helpers, or concrete
    scope infrastructure adapters.
    """

    id: SpecxRuleId = SpecxRuleId.DELIVERY_CONTROLLERS_DO_NOT_IMPORT_INFRASTRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "delivery").glob("**/controllers/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            for module in _explicit_import_modules(context.tree(path)):
                if "infrastructure" in module_parts(module):
                    violations.append(
                        _violation(self.id, path=path, message=f"imports {module}"),
                    )
        delivery_root = context.src_root / "delivery"
        for filename in ("__main__.py", "factory.py", "lifecycle.py"):
            for path in delivery_root.glob(f"*/{filename}"):
                if path not in context.ast_project.files:
                    continue
                for module in _explicit_import_modules(context.tree(path)):
                    if _is_scope_technical_import(module):
                        violations.append(
                            _violation(self.id, path=path, message=f"imports {module}"),
                        )
        return tuple(violations)
