from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
RENDERER = (
    PROJECT_ROOT / "skills" / "specx-tests" / "references" / "render_architecture_guardrails.py"
)


def test_compatibility_renderer_outputs_tiny_wrapper(tmp_path: Path) -> None:
    output = tmp_path / "tests" / "guardrails" / "architecture" / "test_boundaries.py"

    _run_renderer(package_name="demo_service", output=output, check=True)

    text = output.read_text(encoding="utf-8")

    assert "parents[3]" in text
    assert 'package_name="demo_service"' in text
    assert "assert_specx_architecture" in text
    assert len(text.splitlines()) < 25
    assert (tmp_path / "tests" / "__init__.py").read_text(encoding="utf-8") == ""
    assert (tmp_path / "tests" / "guardrails" / "__init__.py").read_text(encoding="utf-8") == ""
    assert (tmp_path / "tests" / "guardrails" / "architecture" / "__init__.py").read_text(
        encoding="utf-8"
    ) == ""


def test_compatibility_renderer_calculates_project_root_for_shallow_output(
    tmp_path: Path,
) -> None:
    output = tmp_path / "tests" / "architecture" / "test_boundaries.py"

    _run_renderer(package_name="demo_service", output=output, check=True)

    assert "parents[2]" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize("package_name", ["bad-name", "class"])
def test_compatibility_renderer_rejects_invalid_package_names(
    tmp_path: Path,
    package_name: str,
) -> None:
    output = tmp_path / "tests" / "architecture" / "test_boundaries.py"

    result = _run_renderer(package_name=package_name, output=output, check=False)

    assert result.returncode != 0
    assert "non-keyword Python package identifier" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize(
    "relative_output",
    ["architecture/test_boundaries.py", "tests/architecture/__init__.py"],
)
def test_compatibility_renderer_rejects_invalid_output_locations(
    tmp_path: Path,
    relative_output: str,
) -> None:
    output = tmp_path / relative_output

    result = _run_renderer(package_name="demo_service", output=output, check=False)

    assert result.returncode != 0
    assert not output.exists()


def _run_renderer(
    *,
    package_name: str,
    output: Path,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--package",
            package_name,
            "--output",
            str(output),
        ],
        check=check,
        capture_output=True,
        text=True,
    )
