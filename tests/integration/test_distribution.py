from __future__ import annotations

import subprocess
from pathlib import Path
from zipfile import ZipFile


def test_wheel_contains_project_initializer_templates(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "--wheel", "--no-sources", "--out-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = tuple(tmp_path.glob("specx-*.whl"))

    assert len(wheels) == 1
    with ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())

    template_root = "specx/_internal/templates/project"
    assert {
        f"{template_root}/agents.md.template",
        f"{template_root}/check_health.py.template",
        f"{template_root}/container.py.template",
        f"{template_root}/gitignore.template",
        f"{template_root}/health_status_dto.py.template",
        f"{template_root}/health_status_enum.py.template",
        f"{template_root}/health_status_service.py.template",
        f"{template_root}/makefile.template",
        f"{template_root}/pyproject.toml.template",
        f"{template_root}/python-version.template",
        f"{template_root}/readme.md.template",
        f"{template_root}/test_check_health.py.template",
        f"{template_root}/test_health_status_service.py.template",
        f"{template_root}/unit_conftest.py.template",
    } <= names
    assert f"{template_root}/test_package.py.template" not in names
