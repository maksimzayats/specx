from __future__ import annotations

import ast
from pathlib import Path

from specx.testing.architecture.context import (
    ArchitectureContext,
    class_base_name_index,
    uses_diwire_container,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _class_can_inject_container,
    _class_injects_diwire_container,
    _is_delivery_composition_module,
    _violation,
)


class OnlyIOCDeliveryAppAndTestsImportContainerRule(ArchitectureRuleBase):
    """Restrict `diwire.Container` imports to composition and tests.

    Application classes should receive dependencies rather than importing the
    container or resolving collaborators directly. A delivery lifecycle is the
    narrow exception because it owns app shutdown and closes the container.
    """

    id: SpecxRuleId = SpecxRuleId.ONLY_IOC_DELIVERY_APP_AND_TESTS_IMPORT_CONTAINER

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in context.source_paths():
            if not uses_diwire_container(context.tree(path)):
                continue
            relative = path.relative_to(context.src_root)
            allowed = relative == Path("ioc/container.py") or _is_delivery_composition_module(
                relative
            )
            if not allowed:
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message="imports diwire.Container outside allowed composition modules",
                    )
                )

            aliases = context.aliases(path)
            for class_node in [
                node for node in ast.walk(context.tree(path)) if isinstance(node, ast.ClassDef)
            ]:
                if _class_injects_diwire_container(
                    class_node,
                    aliases,
                ) and not _class_can_inject_container(
                    relative,
                    class_node,
                    base_index,
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="injects diwire.Container outside delivery lifecycle",
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)
