from __future__ import annotations

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


class CoreDoesNotContainDeliveryPackagesRule(ArchitectureRuleBase):
    """Reject delivery packages nested under core scopes.

    Top-level delivery owns framework translation, while core scopes remain
    framework-free application boundaries.
    """

    id: SpecxRuleId = SpecxRuleId.CORE_DOES_NOT_CONTAIN_DELIVERY_PACKAGES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        return tuple(
            _violation(self.id, path=path, message="core scope contains delivery package")
            for path in (context.src_root / "core").glob("*/delivery")
        )
