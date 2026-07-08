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
        help="Import package name, for example task_db_service.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path, for example tests/guardrails/architecture/test_boundaries.py.",
    )
    args = parser.parse_args()

    if PACKAGE_PATTERN.fullmatch(args.package) is None:
        parser.error("--package must be one Python package identifier, such as task_db_service")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        WRAPPER_TEMPLATE.format(package_name=args.package),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
