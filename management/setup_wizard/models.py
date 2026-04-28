from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal


class StorageMode(StrEnum):
    LOCAL = "local"
    MINIO = "minio"
    REMOTE_S3 = "remote-s3"


@dataclass(frozen=True, kw_only=True)
class SetupAnswers:
    project_name: str
    package_name: str
    distribution_name: str
    docs_site_url: str | None
    storage_mode: StorageMode
    keep_docs: bool
    delete_wizard: bool
    overwrite_env: bool

    s3_endpoint_url: str | None = None
    s3_public_endpoint_url: str | None = None
    s3_region_name: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_public_bucket_name: str = "public"
    s3_protected_bucket_name: str = "protected"


@dataclass(frozen=True, kw_only=True)
class FileOperation:
    kind: Literal["write", "delete", "rename", "command"]
    path: Path
    detail: str
    target_path: Path | None = None
    content: str | None = None
    command: tuple[str, ...] | None = None
