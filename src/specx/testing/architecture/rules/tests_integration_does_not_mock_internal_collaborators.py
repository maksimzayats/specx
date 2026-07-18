from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    function_mocks_internal_app_collaborator,
    local_function_return_annotations,
    violation,
)


class IntegrationTestsDoNotMockInternalCollaboratorsRule(ArchitectureRuleBase):
    """Require integration tests to exercise the real internal application graph.

    Integration tests may stub external systems, but internal use cases,
    services, and capabilities should be resolved through the real container so
    delivery, DI, transaction, and persistence behavior are covered together.
    """

    id: SpecxRuleId = SpecxRuleId.INTEGRATION_TESTS_DO_NOT_MOCK_INTERNAL_COLLABORATORS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        integration_root = context.project_root / "tests" / "integration"
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(integration_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            imports = context.imports(path)
            factory_return_annotations = local_function_return_annotations(tree, aliases)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if function_mocks_internal_app_collaborator(
                    node,
                    aliases,
                    imports,
                    context.config.package_name,
                    factory_return_annotations,
                ):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=(
                                "mocks internal use case, service, or capability in "
                                "integration tests; use the real app graph"
                            ),
                        )
                    )
        return tuple(violations)
