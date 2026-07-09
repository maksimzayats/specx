from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("skills")
    failures: list[str] = []

    if not root.is_dir():
        failures.append(f"{root}: skills directory does not exist")
        return _finish(failures=failures)

    skill_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not skill_dirs:
        failures.append(f"{root}: no skill directories found")
        return _finish(failures=failures)

    for skill_dir in skill_dirs:
        failures.extend(_validate_skill(skill_dir=skill_dir))

    return _finish(failures=failures)


def _validate_skill(*, skill_dir: Path) -> list[str]:
    failures: list[str] = []
    skill_name = skill_dir.name

    if not SKILL_NAME_PATTERN.fullmatch(skill_name):
        failures.append(f"{skill_dir}: skill directory name must be lowercase kebab-case")

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        failures.append(f"{skill_dir}: missing SKILL.md")
        return failures

    text = skill_file.read_text(encoding="utf-8")
    if "TODO" in text:
        failures.append(f"{skill_file}: contains TODO placeholder text")

    frontmatter = _frontmatter(text=text)
    if frontmatter is None:
        failures.append(f"{skill_file}: missing YAML frontmatter")
        return failures

    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        failures.append(f"{skill_file}: frontmatter must be a mapping")
        return failures

    allowed_keys = {"name", "description"}
    unexpected_keys = set(metadata) - allowed_keys
    if unexpected_keys:
        failures.append(f"{skill_file}: unexpected frontmatter keys {sorted(unexpected_keys)}")

    name = metadata.get("name")
    if name != skill_name:
        failures.append(f"{skill_file}: name must match directory name")

    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        failures.append(f"{skill_file}: description is required")
    elif "<" in description or ">" in description:
        failures.append(f"{skill_file}: description cannot contain angle brackets")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        failures.extend(_validate_openai_yaml(path=openai_yaml, skill_name=skill_name))

    return failures


def _frontmatter(*, text: str) -> str | None:
    if not text.startswith("---\n"):
        return None

    end_marker = text.find("\n---\n", 4)
    if end_marker == -1:
        return None

    return text[4:end_marker]


def _validate_openai_yaml(*, path: Path, skill_name: str) -> list[str]:
    failures: list[str] = []
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [f"{path}: must contain a YAML mapping"]

    interface = data.get("interface")
    if not isinstance(interface, dict):
        return [f"{path}: missing interface mapping"]

    default_prompt = interface.get("default_prompt")
    if not isinstance(default_prompt, str) or f"${skill_name}" not in default_prompt:
        failures.append(f"{path}: default_prompt must mention ${skill_name}")

    short_description = interface.get("short_description")
    if not isinstance(short_description, str) or not 25 <= len(short_description) <= 64:
        failures.append(f"{path}: short_description must be 25-64 characters")

    return failures


def _finish(*, failures: list[str]) -> int:
    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("All skills are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
