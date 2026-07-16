from __future__ import annotations

import argparse
import keyword
import re
from pathlib import Path

PACKAGE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
WRAPPER_TEMPLATE = """from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    assert_specx_architecture,
)


def test_specx_architecture() -> None:
    disabled_rules: frozenset[SpecxRuleId] = frozenset()

    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=Path(__file__).resolve().parents[{project_root_parent_index}],
            package_name="{package_name}",
            extend_select=frozenset({{"fastapi"}}),
            disabled_rules=disabled_rules,
        )
    )
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the Specx architecture guardrail pytest module.",
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Import package name, for example url_shortener_service.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path, for example tests/guardrails/architecture/test_boundaries.py.",
    )
    args = parser.parse_args()

    if PACKAGE_PATTERN.fullmatch(args.package) is None or keyword.iskeyword(args.package):
        parser.error(
            "--package must be one non-keyword Python package identifier, "
            "such as url_shortener_service"
        )
    if args.output.suffix != ".py" or args.output.name == "__init__.py":
        parser.error("--output must be a Python test module, not __init__.py")

    tests_root = _tests_root(args.output)
    if tests_root is None:
        parser.error("--output must be inside the project's tests directory")

    resolved_output = args.output.resolve()
    project_root_parent_index = len(resolved_output.parent.relative_to(tests_root.parent).parts)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    for directory in _test_package_directories(args.output, tests_root=tests_root):
        (directory / "__init__.py").touch(exist_ok=True)
    args.output.write_text(
        WRAPPER_TEMPLATE.format(
            package_name=args.package,
            project_root_parent_index=project_root_parent_index,
        ),
        encoding="utf-8",
    )
    return 0


def _tests_root(output: Path) -> Path | None:
    resolved_output = output.resolve()
    return next(
        (directory for directory in resolved_output.parents if directory.name == "tests"),
        None,
    )


def _test_package_directories(output: Path, *, tests_root: Path) -> tuple[Path, ...]:
    resolved_output = output.resolve()

    return tuple(
        directory
        for directory in reversed(resolved_output.parents)
        if directory == tests_root or tests_root in directory.parents
    )


if __name__ == "__main__":
    raise SystemExit(main())
