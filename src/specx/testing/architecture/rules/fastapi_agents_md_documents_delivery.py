from __future__ import annotations

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _violation,
)


class FastAPIRootAgentsMDDocumentsDeliveryRule(ArchitectureRuleBase):
    """Require FastAPI projects to document their delivery entrypoint and lifecycle.

    Technology-specific delivery guidance is opt-in so framework-neutral
    projects keep the core Specx architecture contract without fake FastAPI paths.
    """

    id: SpecxRuleId = SpecxRuleId.FASTAPI_ROOT_AGENTS_MD_DOCUMENTS_DELIVERY
    family = "fastapi"
    default_enabled = False
    required_project_surface: str | None = "delivery/fastapi"

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        path = context.project_root / "AGENTS.md"
        if not path.exists():
            return (_violation(self.id, path=path, message="AGENTS.md is missing"),)

        normalized_text = " ".join(path.read_text(encoding="utf-8").split())
        required_fragments = {
            f"FastAPI entrypoint: `{context.config.package_name}.delivery.fastapi.__main__:app`",
            "FastAPILifecycle",
            "container.aclose()",
        }
        missing_fragments = sorted(
            fragment
            for fragment in required_fragments
            if " ".join(fragment.split()) not in normalized_text
        )
        if not missing_fragments:
            return ()

        return (_violation(self.id, path=path, message=f"missing fragments {missing_fragments}"),)
