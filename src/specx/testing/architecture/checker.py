from __future__ import annotations

from specx._internal.python_ast.scanner import PythonAstScanner
from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import (
    SpecxArchitectureConfig,
    SpecxArchitectureReport,
    SpecxArchitectureViolation,
)
from specx.testing.architecture.registry import SpecxRuleRegistry


def check_specx_architecture(config: SpecxArchitectureConfig) -> SpecxArchitectureReport:
    """Run enabled Specx architecture rules and return a grouped report."""

    scanner = PythonAstScanner(
        project_root=config.project_root,
        excluded_patterns=config.path_exclusions,
    )
    ast_project = scanner.scan(roots=(config.project_root / "src", config.project_root / "tests"))
    context = ArchitectureContext(config=config, ast_project=ast_project)
    registry = SpecxRuleRegistry.build(extra_rules=config.extra_rules)
    violations: list[SpecxArchitectureViolation] = []

    for rule_type in registry.enabled_rules(disabled_rules=config.disabled_rules):
        rule = rule_type()
        violations.extend(rule.check(context))

    return SpecxArchitectureReport(
        project_root=config.project_root,
        violations=tuple(violations),
    )


def assert_specx_architecture(config: SpecxArchitectureConfig) -> None:
    """Assert that a project satisfies every enabled Specx architecture rule."""

    report = check_specx_architecture(config)
    if report.has_violations:
        raise AssertionError(report.format())
