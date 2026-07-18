from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _fixture_bundles_mocks,
    _is_pytest_fixture,
    _violation,
)


class TestFixturesDoNotBundleMocksRule(ArchitectureRuleBase):
    """Reject grouped mock fixtures in generated-service tests.

    A mock fixture should override one collaborator for the behavior under
    test. Class-keyed dictionaries of unrelated mocks make tests unclear about
    what is mocked and what behavior is actually under assertion.
    """

    id: SpecxRuleId = SpecxRuleId.TEST_FIXTURES_DO_NOT_BUNDLE_MOCKS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        test_root = context.project_root / "tests"
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(test_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_pytest_fixture(node, aliases):
                    continue
                if _fixture_bundles_mocks(node, aliases):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=("bundles multiple mocks; use one fixture per collaborator"),
                        )
                    )
        return tuple(violations)
