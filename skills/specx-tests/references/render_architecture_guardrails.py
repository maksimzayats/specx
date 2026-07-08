from __future__ import annotations

import argparse
import re
from pathlib import Path


PACKAGE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PACKAGE_PLACEHOLDER = "__SPECX_PACKAGE_NAME__"
TEMPLATE_PATH = Path(__file__).with_name("architecture_guardrails.py")


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
        help="Output path, for example tests/architecture/test_boundaries.py.",
    )
    args = parser.parse_args()

    if PACKAGE_PATTERN.fullmatch(args.package) is None:
        parser.error(
            "--package must be one Python package identifier, such as task_db_service"
        )

    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = text.replace(PACKAGE_PLACEHOLDER, args.package)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
