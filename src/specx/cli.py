from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from inspect import getdoc
from pathlib import Path
from typing import Any

from specx._internal.cli_config import load_specx_config
from specx._internal.exceptions import BaseSpecxError
from specx._internal.project_init import initialize_project
from specx.testing.architecture import (
    SpecxArchitectureReport,
    SpecxArchitectureViolation,
    SpecxArchitectureWarning,
    SpecxConfigurationError,
    check_specx_architecture,
)
from specx.testing.architecture.registry import SpecxRuleRegistry


def main(argv: Sequence[str] | None = None) -> int:
    """Run the specx command-line interface and return a process exit code."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "check":
            return _run_check(
                project_root=arguments.root,
                output_format=arguments.output_format,
            )
        if arguments.command == "init":
            return _run_init(
                target=arguments.path,
                project_name=arguments.project_name,
                package_name=arguments.package_name,
                python_version=arguments.python_version,
                synchronize=not arguments.no_sync,
            )
        if arguments.command == "rule" and arguments.rule_command == "list":
            return _run_rule_list()
        if arguments.command == "rule" and arguments.rule_command == "explain":
            return _run_rule_explain(arguments.rule_id)
        raise SpecxConfigurationError("a command is required")
    except (BaseSpecxError, OSError, SyntaxError) as error:
        print(f"specx error: {error}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specx",
        description="Enforce architecture and test guardrails for Python projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="check a complete Python project")
    check_parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root containing pyproject.toml (default: current directory)",
    )
    check_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="diagnostic output format (default: text)",
    )

    init_parser = subparsers.add_parser(
        "init",
        help="initialize a new framework-neutral Python project",
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="new project directory (default: current directory)",
    )
    init_parser.add_argument(
        "--name",
        dest="project_name",
        help="distribution name (default: normalized target directory name)",
    )
    init_parser.add_argument(
        "--package",
        dest="package_name",
        help="lowercase Python import package (default: derived from project name)",
    )
    init_parser.add_argument(
        "--python",
        dest="python_version",
        default="3.14",
        help="Python major.minor version (default: 3.14)",
    )
    init_parser.add_argument(
        "--no-sync",
        action="store_true",
        help="write project files without adding runtime or dev dependencies",
    )

    rule_parser = subparsers.add_parser("rule", help="inspect built-in architecture rules")
    rule_subparsers = rule_parser.add_subparsers(dest="rule_command", required=True)
    rule_subparsers.add_parser("list", help="list built-in architecture rules")
    explain_parser = rule_subparsers.add_parser("explain", help="explain one rule")
    explain_parser.add_argument("rule_id", help="exact semantic rule identifier")
    return parser


def _run_init(
    *,
    target: Path,
    project_name: str | None,
    package_name: str | None,
    python_version: str,
    synchronize: bool,
) -> int:
    initialized = initialize_project(
        target,
        project_name=project_name,
        package_name=package_name,
        python_version=python_version,
        synchronize=synchronize,
    )
    print(f"Initialized project {initialized.project_name!r} at {initialized.root}")
    print(f"Package: {initialized.package_name}")
    print(f"Python: {initialized.python_version}")
    if initialized.synchronized:
        print("Dependencies added with `uv add specx diwire` and `uv add --dev mypy pytest ruff`.")
        print(f"Next: run `make check` from {initialized.root}")
    else:
        print(f"Next: run `uv add specx diwire` from {initialized.root}.")
        print("Then run `uv add --dev mypy pytest ruff` and `make check`.")
    return 0


def _run_check(*, project_root: Path, output_format: str) -> int:
    loaded = load_specx_config(project_root)
    report = check_specx_architecture(loaded.architecture)

    if output_format == "json":
        print(_format_json(report))
    else:
        print(_format_text(report))
    return 1 if report.has_violations else 0


def _run_rule_list() -> int:
    registry = SpecxRuleRegistry.build()
    sorted_rules = sorted(
        registry.rules,
        key=lambda candidate: str(candidate.metadata().rule_id),
    )
    for rule_type in sorted_rules:
        metadata = rule_type.metadata()
        status = "default" if metadata.default_enabled else "opt-in"
        print(f"{metadata.rule_id} [{metadata.family}, {status}] {metadata.summary}")
    return 0


def _run_rule_explain(rule_id: str) -> int:
    registry = SpecxRuleRegistry.build()
    rule_type = next(
        (candidate for candidate in registry.rules if str(candidate.metadata().rule_id) == rule_id),
        None,
    )
    if rule_type is None:
        available = ", ".join(sorted(str(rule.metadata().rule_id) for rule in registry.rules))
        raise SpecxConfigurationError(f"unknown rule {rule_id!r}; available rules: {available}")

    metadata = rule_type.metadata()
    print(f"Rule: {metadata.rule_id}")
    print(f"Family: {metadata.family}")
    print(f"Enabled by default: {'yes' if metadata.default_enabled else 'no'}")
    if metadata.required_project_surface is not None:
        print(f"Required project surface: {metadata.required_project_surface}")
    print()
    print(getdoc(rule_type) or metadata.summary)
    return 0


def _format_text(report: SpecxArchitectureReport) -> str:
    lines = [
        _format_text_diagnostic(
            project_root=report.project_root,
            severity="warning",
            diagnostic=warning,
        )
        for warning in report.warnings
    ]
    lines.extend(
        _format_text_diagnostic(
            project_root=report.project_root,
            severity="error",
            diagnostic=violation,
        )
        for violation in report.violations
    )
    if report.has_violations:
        lines.append(
            f"Found {len(report.violations)} violation(s) and {len(report.warnings)} warning(s)."
        )
    else:
        lines.append(f"specx checks passed with {len(report.warnings)} warning(s).")
    return "\n".join(lines)


def _format_text_diagnostic(
    *,
    project_root: Path,
    severity: str,
    diagnostic: SpecxArchitectureViolation | SpecxArchitectureWarning,
) -> str:
    location = ""
    if diagnostic.path is not None:
        try:
            location = diagnostic.path.relative_to(project_root).as_posix()
        except ValueError:
            location = str(diagnostic.path)
    if diagnostic.line is not None:
        location = f"{location}:{diagnostic.line}"
        if diagnostic.column is not None:
            location = f"{location}:{diagnostic.column}"
    prefix = f"{location}: " if location else ""
    return f"{prefix}{severity} {diagnostic.rule_id} {diagnostic.message}"


def _format_json(report: SpecxArchitectureReport) -> str:
    diagnostics = [
        _json_diagnostic(
            project_root=report.project_root,
            severity="warning",
            diagnostic=warning,
        )
        for warning in report.warnings
    ]
    diagnostics.extend(
        _json_diagnostic(
            project_root=report.project_root,
            severity="error",
            diagnostic=violation,
        )
        for violation in report.violations
    )
    payload = {
        "version": 1,
        "root": str(report.project_root),
        "diagnostics": diagnostics,
        "summary": {
            "errors": len(report.violations),
            "warnings": len(report.warnings),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _json_diagnostic(
    *,
    project_root: Path,
    severity: str,
    diagnostic: SpecxArchitectureViolation | SpecxArchitectureWarning,
) -> dict[str, Any]:
    values = asdict(diagnostic)
    path = values.pop("path")
    values.pop("symbol", None)
    values["rule_id"] = str(values["rule_id"])
    values["severity"] = severity
    if path is None:
        values["path"] = None
    else:
        try:
            values["path"] = path.relative_to(project_root).as_posix()
        except ValueError:
            values["path"] = str(path)
    return values
