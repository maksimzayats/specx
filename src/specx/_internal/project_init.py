from __future__ import annotations

import keyword
import re
import shutil
import subprocess
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from specx._internal.exceptions import BaseSpecxError

_DEFAULT_PYTHON_VERSION = "3.14"
_DISTRIBUTION_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")
_PACKAGE_NAME_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")
_PYTHON_VERSION_PATTERN = re.compile(r"[1-9]\d*\.\d+")
_TEMPLATE_PACKAGE = "specx._internal.templates.project"
_TEMPLATE_DESTINATIONS = {
    "agents.md.template": Path("AGENTS.md"),
    "check_health.py.template": Path(
        "src/__SPECX_PACKAGE_NAME__/core/health/use_cases/check_health.py"
    ),
    "container.py.template": Path("src/__SPECX_PACKAGE_NAME__/ioc/container.py"),
    "gitignore.template": Path(".gitignore"),
    "health_status_dto.py.template": Path(
        "src/__SPECX_PACKAGE_NAME__/core/health/dtos/health_status_dto.py"
    ),
    "health_status_enum.py.template": Path(
        "src/__SPECX_PACKAGE_NAME__/core/health/enums/health_status_enum.py"
    ),
    "health_status_service.py.template": Path(
        "src/__SPECX_PACKAGE_NAME__/core/health/services/health_status_service.py"
    ),
    "makefile.template": Path("Makefile"),
    "pyproject.toml.template": Path("pyproject.toml"),
    "python-version.template": Path(".python-version"),
    "readme.md.template": Path("README.md"),
    "test_check_health.py.template": Path("tests/unit/core/health/use_cases/test_check_health.py"),
    "test_health_status_service.py.template": Path(
        "tests/unit/core/health/services/test_health_status_service.py"
    ),
    "unit_conftest.py.template": Path("tests/unit/conftest.py"),
}

_EMPTY_PACKAGE_DIRECTORIES = (
    "src/__SPECX_PACKAGE_NAME__",
    "src/__SPECX_PACKAGE_NAME__/core",
    "src/__SPECX_PACKAGE_NAME__/core/health",
    "src/__SPECX_PACKAGE_NAME__/core/health/dtos",
    "src/__SPECX_PACKAGE_NAME__/core/health/enums",
    "src/__SPECX_PACKAGE_NAME__/core/health/services",
    "src/__SPECX_PACKAGE_NAME__/core/health/use_cases",
    "src/__SPECX_PACKAGE_NAME__/ioc",
    "tests",
    "tests/unit",
    "tests/unit/core",
    "tests/unit/core/health",
    "tests/unit/core/health/services",
    "tests/unit/core/health/use_cases",
)


class SpecxInitializationError(BaseSpecxError):
    """Raised when a new specx project cannot be initialized safely."""


@dataclass(frozen=True, kw_only=True, slots=True)
class InitializedProject:
    """Resolved details for a newly initialized specx project."""

    root: Path
    project_name: str
    package_name: str
    python_version: str
    synchronized: bool


def initialize_project(
    target: Path,
    *,
    project_name: str | None = None,
    package_name: str | None = None,
    python_version: str = _DEFAULT_PYTHON_VERSION,
    synchronize: bool = True,
) -> InitializedProject:
    """Create one fresh, framework-neutral specx project."""

    root = _validate_target(target)
    resolved_project_name = normalize_project_name(project_name or root.name)
    resolved_package_name = (
        validate_package_name(package_name)
        if package_name is not None
        else package_name_from_project_name(resolved_project_name)
    )
    resolved_python_version = validate_python_version(python_version)

    if synchronize and shutil.which("uv") is None:
        raise SpecxInitializationError(
            "uv is required to initialize the environment; install uv or pass --no-sync"
        )

    rendered_files = _render_project_files(
        project_name=resolved_project_name,
        package_name=resolved_package_name,
        python_version=resolved_python_version,
    )
    _write_project(root, rendered_files=rendered_files)

    if synchronize:
        _add_project_dependencies(root)

    return InitializedProject(
        root=root,
        project_name=resolved_project_name,
        package_name=resolved_package_name,
        python_version=resolved_python_version,
        synchronized=synchronize,
    )


def normalize_project_name(value: str) -> str:
    """Normalize a display or directory name to lowercase kebab-case."""

    normalized = _DISTRIBUTION_SEPARATOR_PATTERN.sub("-", value.lower()).strip("-")
    if not normalized:
        raise SpecxInitializationError(
            "project name must contain at least one ASCII letter or number"
        )
    return normalized


def package_name_from_project_name(project_name: str) -> str:
    """Derive a deterministic import package from a normalized project name."""

    package_name = project_name.replace("-", "_")
    if package_name[0].isdigit():
        package_name = f"_{package_name}"
    if keyword.iskeyword(package_name):
        package_name = f"{package_name}_package"
    return validate_package_name(package_name)


def validate_package_name(value: str) -> str:
    """Validate an explicit lowercase ASCII Python import package name."""

    if (
        _PACKAGE_NAME_PATTERN.fullmatch(value) is None
        or keyword.iskeyword(value)
        or not any(character.isalnum() for character in value)
    ):
        raise SpecxInitializationError(
            "package must be a lowercase ASCII Python identifier and not a keyword"
        )
    return value


def validate_python_version(value: str) -> str:
    """Validate the shape of a generated-project Python minor version."""

    if _PYTHON_VERSION_PATTERN.fullmatch(value) is None:
        raise SpecxInitializationError(
            f"invalid Python version {value!r}; expected a major.minor value such as 3.15"
        )
    return value


def _validate_target(target: Path) -> Path:
    expanded = target.expanduser()
    if expanded.is_symlink():
        raise SpecxInitializationError(f"project target must not be a symlink: {expanded}")

    root = expanded.resolve()
    if root.exists() and not root.is_dir():
        raise SpecxInitializationError(f"project target is not a directory: {root}")
    if not root.exists():
        return root

    entries = tuple(root.iterdir())
    unexpected_entries = tuple(path for path in entries if path.name != ".git")
    git_entry = next((path for path in entries if path.name == ".git"), None)
    if unexpected_entries or (git_entry is not None and not git_entry.is_dir()):
        raise SpecxInitializationError(
            f"project target must be empty or contain only a .git directory: {root}"
        )
    return root


def _render_project_files(
    *,
    project_name: str,
    package_name: str,
    python_version: str,
) -> dict[Path, str]:
    replacements = {
        "__SPECX_PACKAGE_NAME__": package_name,
        "__SPECX_PROJECT_NAME__": project_name,
        "__SPECX_PYTHON_TARGET__": python_version.replace(".", ""),
        "__SPECX_PYTHON_VERSION__": python_version,
    }
    template_root = resources.files(_TEMPLATE_PACKAGE)
    rendered_files: dict[Path, str] = {}
    for template_name, destination in _TEMPLATE_DESTINATIONS.items():
        template = template_root.joinpath(template_name)
        if not template.is_file():
            raise SpecxInitializationError(f"packaged project template is missing: {template_name}")
        text = template.read_text(encoding="utf-8")
        for token, replacement in replacements.items():
            text = text.replace(token, replacement)
        destination_text = destination.as_posix()
        for token, replacement in replacements.items():
            destination_text = destination_text.replace(token, replacement)
        rendered_files[Path(destination_text)] = text

    for package_directory in _EMPTY_PACKAGE_DIRECTORIES:
        rendered_files[
            Path(package_directory.replace("__SPECX_PACKAGE_NAME__", package_name)) / "__init__.py"
        ] = ""
    return rendered_files


def _write_project(root: Path, *, rendered_files: dict[Path, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for relative_path, text in rendered_files.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as output:
            output.write(text)


def _add_project_dependencies(root: Path) -> None:
    commands = (
        ("uv", "add", "specx", "diwire"),
        ("uv", "add", "--dev", "mypy", "pytest", "ruff"),
    )
    for command in commands:
        try:
            subprocess.run(
                command,
                cwd=root,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            rendered_command = " ".join(command)
            raise SpecxInitializationError(
                f"{rendered_command} failed with exit code {error.returncode}; "
                f"project files remain at {root}; rerun the command there"
            ) from error
