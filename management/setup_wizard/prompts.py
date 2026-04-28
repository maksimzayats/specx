from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import cast

import questionary

from management.setup_wizard.models import SetupAnswers, StorageMode

PACKAGE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
DISTRIBUTION_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*[a-z0-9]$")
TEMPLATE_PROJECT_NAME = "Fast Django"
TEMPLATE_PACKAGE_NAME = "fastdjango"
TEMPLATE_DISTRIBUTION_NAME = "fastdjango"


def prompt_for_answers(*, repo_root: Path) -> SetupAnswers:
    project_name = _ask_text(
        f"Project name (replace template default: {TEMPLATE_PROJECT_NAME})",
        validate=_validate_project_name,
    )
    package_name = _ask_text(
        f"Python package name (replace template default: {TEMPLATE_PACKAGE_NAME})",
        validate=_validate_package_name,
    )
    suggested_distribution_name = package_name.strip().replace("_", "-")
    distribution_name = _ask_text(
        "Distribution name",
        default=suggested_distribution_name,
        validate=_validate_distribution_name,
    )
    keep_docs = _ask_confirm("Keep documentation?", default=True)
    docs_site_url = _ask_docs_site_url(keep_docs=keep_docs)
    storage_mode = _ask_storage_mode()
    storage_answers = _ask_remote_s3_answers(storage_mode=storage_mode)
    delete_wizard = _ask_confirm("Delete setup wizard after setup?", default=True)
    overwrite_env = _ask_overwrite_env(repo_root=repo_root)

    return SetupAnswers(
        project_name=project_name.strip(),
        package_name=package_name.strip(),
        distribution_name=distribution_name.strip(),
        docs_site_url=docs_site_url,
        storage_mode=storage_mode,
        keep_docs=keep_docs,
        delete_wizard=delete_wizard,
        overwrite_env=overwrite_env,
        **storage_answers,
    )


def confirm_plan() -> bool:
    return _ask_confirm("Apply these changes?", default=False)


def _ask_storage_mode() -> StorageMode:
    value = questionary.select(
        "Storage mode",
        choices=[
            questionary.Choice("Local filesystem", StorageMode.LOCAL),
            questionary.Choice("Local MinIO", StorageMode.MINIO),
            questionary.Choice("Remote S3-compatible", StorageMode.REMOTE_S3),
        ],
        default=StorageMode.LOCAL,
    ).ask()
    if value is None:
        raise KeyboardInterrupt

    return cast(StorageMode, value)


def _ask_remote_s3_answers(*, storage_mode: StorageMode) -> dict[str, str]:
    if storage_mode != StorageMode.REMOTE_S3:
        return {}

    return {
        "s3_endpoint_url": _ask_text(
            "S3 endpoint URL (example: https://s3.example.com)",
            validate=_validate_required_text,
        ),
        "s3_public_endpoint_url": _ask_text(
            "Public S3 endpoint URL (example: https://cdn.example.com)",
            validate=_validate_required_text,
        ),
        "s3_region_name": _ask_text(
            "S3 region (example: us-east-1)",
            validate=_validate_required_text,
        ),
        "s3_access_key_id": _ask_text("S3 access key ID", validate=_validate_required_text),
        "s3_secret_access_key": _ask_text("S3 secret access key", validate=_validate_required_text),
        "s3_public_bucket_name": _ask_text("Public bucket (blank uses: public)") or "public",
        "s3_protected_bucket_name": _ask_text("Protected bucket (blank uses: protected)")
        or "protected",
    }


def _ask_docs_site_url(*, keep_docs: bool) -> str | None:
    if not keep_docs:
        return None

    return _optional_text("Docs site URL (optional; blank keeps docs local-only for now)")


def _ask_overwrite_env(*, repo_root: Path) -> bool:
    if not (repo_root / ".env").exists():
        return True

    return _ask_confirm("Overwrite existing .env?", default=False)


def _ask_text(
    message: str,
    *,
    default: str = "",
    validate: QuestionaryValidator | None = None,
) -> str:
    value = questionary.text(message, default=default, validate=validate).ask()
    if value is None:
        raise KeyboardInterrupt

    return value


def _optional_text(message: str) -> str | None:
    value = _ask_text(message, default="")
    value = value.strip()
    return value or None


def _ask_confirm(message: str, *, default: bool) -> bool:
    value = questionary.confirm(message, default=default).ask()
    if value is None:
        raise KeyboardInterrupt

    return bool(value)


def _validate_package_name(value: str) -> bool | str:
    value = value.strip()
    if value == TEMPLATE_PACKAGE_NAME:
        return "Replace the template package name with your own package name."

    if PACKAGE_NAME_PATTERN.fullmatch(value):
        return True

    return "Use a valid lowercase Python package name, like my_api."


def _validate_distribution_name(value: str) -> bool | str:
    value = value.strip()
    if value == TEMPLATE_DISTRIBUTION_NAME:
        return "Replace the template distribution name with your own distribution name."

    if DISTRIBUTION_NAME_PATTERN.fullmatch(value):
        return True

    return "Use a valid package distribution name, like my-api."


def _validate_project_name(value: str) -> bool | str:
    value = value.strip()
    if not value:
        return "Project name is required."

    if value.casefold() == TEMPLATE_PROJECT_NAME.casefold():
        return "Replace the template project name with your own project name."

    return True


def _validate_required_text(value: str) -> bool | str:
    if value.strip():
        return True

    return "This value is required."


type QuestionaryValidator = Callable[[str], bool | str]
