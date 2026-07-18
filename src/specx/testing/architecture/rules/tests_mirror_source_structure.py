from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _fixture_returns_use_closure,
    _flat_test_path_for_source_path,
    _is_allowed_mirrored_fake_module_path,
    _is_core_behavior_target_test_path,
    _is_core_behavior_test_path,
    _is_fake_module_path,
    _is_non_source_integration_test,
    _is_pytest_fixture,
    _is_target_specific_test_factory_or_harness,
    _is_test_double_class_name,
    _mirrored_test_paths,
    _required_integration_test_source_paths,
    _required_unit_test_source_paths,
    _source_paths_for_test_path,
    _support_fakes_package_exists,
    _target_folder_test_exists,
    _violation,
)


class TestsMirrorSourceStructureRule(ArchitectureRuleBase):
    """Require meaningful generated-service tests to mirror source modules.

    The required generated scope is core services, use cases, and capabilities.
    Existing unit and integration tests still need to mirror source modules so
    behavior ownership stays explicit without forcing infrastructure filler.
    """

    id: SpecxRuleId = SpecxRuleId.TESTS_MIRROR_SOURCE_STRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        violations.extend(self._unmapped_test_violations(context))
        violations.extend(self._test_support_structure_violations(context))
        violations.extend(self._missing_required_test_violations(context))
        return tuple(violations)

    def _unmapped_test_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for test_root_name in ("unit", "integration"):
            test_root = context.project_root / "tests" / test_root_name
            if not test_root.exists():
                continue
            for path in _mirrored_test_paths(context, test_root=test_root):
                if _is_non_source_integration_test(path, test_root=test_root):
                    continue
                relative = path.relative_to(test_root)
                if _is_core_behavior_test_path(relative):
                    if path.name.startswith("test_") and _is_core_behavior_target_test_path(
                        relative
                    ):
                        expected_path = test_root / relative.parent.parent / relative.name
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=(
                                    "core behavior test must be flat; expected "
                                    f"{expected_path.relative_to(context.project_root)}"
                                ),
                            )
                        )
                        continue
                    source_paths = _source_paths_for_test_path(
                        path,
                        test_root=test_root,
                        src_root=context.src_root,
                    )
                    if not any(
                        source_path in context.ast_project.files for source_path in source_paths
                    ):
                        violations.append(
                            _violation(
                                self.id,
                                path=path,
                                message=(
                                    "test does not mirror a source module; expected "
                                    f"{source_paths[0].relative_to(context.project_root)}"
                                ),
                            )
                        )
                    continue
                source_paths = _source_paths_for_test_path(
                    path,
                    test_root=test_root,
                    src_root=context.src_root,
                )
                if not any(
                    source_path in context.ast_project.files for source_path in source_paths
                ):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message=(
                                "test does not mirror a source module; expected "
                                f"{source_paths[0].relative_to(context.project_root)}"
                            ),
                        )
                    )
        return tuple(violations)

    def _test_support_structure_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        test_root = context.project_root / "tests"
        support_root = test_root / "_support"
        support_fakes_root = support_root / "fakes"
        if _support_fakes_package_exists(support_fakes_root):
            violations.append(
                _violation(
                    self.id,
                    path=support_fakes_root,
                    message=(
                        "tests/_support/fakes is not allowed; keep one-off doubles in test "
                        "modules and reused unit doubles in mirrored fake_<source_module>.py "
                        "modules"
                    ),
                )
            )
        for path in sorted(context.ast_project.files):
            if not path.is_relative_to(test_root) or path.name == "__init__.py":
                continue
            tree = context.tree(path)
            aliases = context.aliases(path)
            if path.name == "harness.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "harness.py is not allowed; resolve targets directly from the "
                            "container in flat test modules"
                        ),
                    )
                )
            if path.name == "_fakes.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "shared _fakes.py files are not allowed; use mirrored "
                            "fake_<source_module>.py modules for reused unit doubles"
                        ),
                    )
                )
            if _is_fake_module_path(path) and not _is_allowed_mirrored_fake_module_path(
                path,
                test_root=test_root,
            ):
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "fake_*.py modules are allowed only under tests/unit/core "
                            "capabilities, gateways, or repositories packages and must mirror "
                            "a source module"
                        ),
                    )
                )
            if path.name == "conftest.py":
                for class_node in [
                    node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                ]:
                    if not _is_test_double_class_name(class_node.name):
                        continue
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=class_node.name,
                            message=(
                                "test double classes do not belong in conftest.py; define "
                                "them in the test module that uses them"
                            ),
                        )
                    )
            if path.name == "_scenarios.py":
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        message=(
                            "generic scenario files are not allowed; keep setup in the "
                            "test module that uses it"
                        ),
                    )
                )
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_pytest_fixture(node, aliases):
                    continue
                if _fixture_returns_use_closure(node):
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            symbol=node.name,
                            message=(
                                "closure-style use_* fixture factories are not allowed; "
                                "register overrides directly before container.resolve(...)"
                            ),
                        )
                    )
            if not path.is_relative_to(support_root):
                continue
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                if not _is_target_specific_test_factory_or_harness(class_node.name):
                    continue
                violations.append(
                    _violation(
                        self.id,
                        path=path,
                        symbol=class_node.name,
                        message=(
                            "target-specific test factories and harnesses are not allowed; "
                            "resolve targets directly from the container"
                        ),
                    )
                )
        return tuple(violations)

    def _missing_required_test_violations(
        self,
        context: ArchitectureContext,
    ) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for source_path in _required_unit_test_source_paths(context):
            flat_path = _flat_test_path_for_source_path(
                source_path,
                test_root=context.project_root / "tests" / "unit",
                src_root=context.src_root,
            )
            if flat_path in context.ast_project.files or _target_folder_test_exists(
                flat_path,
                context=context,
            ):
                continue
            violations.append(
                _violation(
                    self.id,
                    path=source_path,
                    message=f"missing unit test {flat_path.relative_to(context.project_root)}",
                )
            )
        for source_path in _required_integration_test_source_paths(context):
            expected_path = _flat_test_path_for_source_path(
                source_path,
                test_root=context.project_root / "tests" / "integration",
                src_root=context.src_root,
            )
            if expected_path in context.ast_project.files or _target_folder_test_exists(
                expected_path,
                context=context,
            ):
                continue
            violations.append(
                _violation(
                    self.id,
                    path=source_path,
                    message=(
                        "missing integration test "
                        f"{expected_path.relative_to(context.project_root)}"
                    ),
                )
            )
        return tuple(violations)
