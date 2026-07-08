from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_compatibility_renderer_outputs_tiny_wrapper(tmp_path: Path) -> None:
    output = tmp_path / "tests" / "architecture" / "test_boundaries.py"

    subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "skills"
                / "specx-tests"
                / "references"
                / "render_architecture_guardrails.py"
            ),
            "--package",
            "demo_service",
            "--output",
            str(output),
        ],
        check=True,
    )

    text = output.read_text(encoding="utf-8")

    assert 'package_name="demo_service"' in text
    assert "assert_specx_architecture" in text
    assert len(text.splitlines()) < 25
