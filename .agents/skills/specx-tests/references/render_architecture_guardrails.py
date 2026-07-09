from __future__ import annotations

import argparse
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
            project_root=Path(__file__).resolve().parents[3],
            package_name="{package_name}",
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

    if PACKAGE_PATTERN.fullmatch(args.package) is None:
        parser.error(
            "--package must be one Python package identifier, such as url_shortener_service"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    for directory in _test_package_directories(args.output):
        (directory / "__init__.py").touch(exist_ok=True)
    args.output.write_text(
        WRAPPER_TEMPLATE.format(package_name=args.package),
        encoding="utf-8",
    )
    return 0


def _test_package_directories(output: Path) -> tuple[Path, ...]:
    resolved_output = output.resolve()
    directories = (resolved_output.parent, *resolved_output.parents)
    tests_root = next((directory for directory in directories if directory.name == "tests"), None)
    if tests_root is None:
        return ()

    return tuple(
        directory
        for directory in reversed(directories)
        if directory == tests_root or tests_root in directory.parents
    )


if __name__ == "__main__":
    raise SystemExit(main())
