from __future__ import annotations

from specx.testing.architecture.context import (
    ArchitectureContext,
    class_base_name_index,
    documented_make_targets,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    project_uses_alembic,
    project_uses_foundation_base,
    required_integration_test_source_paths,
    violation,
)


class RootAgentsMDDocumentsProjectCommandsAndBoundariesRule(ArchitectureRuleBase):
    """Keep generated-project agent guidance aligned with commands and boundaries.

    `AGENTS.md` is part of the generated project contract; it must document the
    runnable commands and core specx rules without drifting from the Makefile.
    """

    id: SpecxRuleId = SpecxRuleId.ROOT_AGENTS_MD_DOCUMENTS_PROJECT_COMMANDS_AND_BOUNDARIES

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        path = context.project_root / "AGENTS.md"
        if not path.exists():
            return (violation(self.id, path=path, message="AGENTS.md is missing"),)
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())
        required_fragments = {
            f"Package lives under `src/{context.config.package_name}`",
            "make check",
            "make lint",
            "make test",
            "LoggingConfigurator",
            "Do not inject loggers",
        }
        base_index = class_base_name_index(context)
        optional_base_fragments = {
            "BaseCapability": "BaseCapability",
            "BaseGateway": "BaseGateway",
            "BasePureService": "BasePureService",
            "BaseReadService": "BaseReadService",
            "BaseEffectService": "BaseEffectService",
        }
        required_fragments.update(
            fragment
            for base, fragment in optional_base_fragments.items()
            if project_uses_foundation_base(base_index, base)
        )
        if project_uses_foundation_base(base_index, "BaseUseCase"):
            required_fragments.add("Use cases return DTOs, not entities")
        if project_uses_foundation_base(base_index, "BaseQuery"):
            required_fragments.add("Query use cases must not call repository mutators")
        if required_integration_test_source_paths(context):
            required_fragments.update(
                {
                    "Use cases that touch persistence inject `UnitOfWorkManager`",
                    "must not inject repositories, active UoWs, providers",
                    "SQLAlchemy sessions/engines/session factories",
                }
            )
        if project_uses_alembic(context):
            required_fragments.update(
                {
                    "make migration-check",
                    "make makemigrations",
                    "Do not use `create_all()` or `drop_all()`",
                }
            )
        violations: list[SpecxArchitectureViolation] = []
        missing_fragments = sorted(
            fragment
            for fragment in required_fragments
            if " ".join(fragment.split()) not in normalized_text
        )
        if missing_fragments:
            violations.append(
                violation(self.id, path=path, message=f"missing fragments {missing_fragments}")
            )
        missing_make_targets = sorted(documented_make_targets(text) - context.makefile_targets())
        if missing_make_targets:
            violations.append(
                violation(
                    self.id,
                    path=path,
                    message=f"documents missing make targets {missing_make_targets}",
                )
            )
        return tuple(violations)
