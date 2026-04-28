from __future__ import annotations

import secrets
from dataclasses import dataclass

from management.setup_wizard.models import SetupAnswers, StorageMode


@dataclass(frozen=True, kw_only=True)
class EnvCredentials:
    django_key: str
    jwt_key: str
    postgres_key: str
    redis_key: str


def build_env_content(*, answers: SetupAnswers) -> str:
    lines = _build_base_env_lines(
        answers=answers,
        credentials=EnvCredentials(
            django_key=secrets.token_urlsafe(48),
            jwt_key=secrets.token_urlsafe(48),
            postgres_key=secrets.token_urlsafe(32),
            redis_key=secrets.token_urlsafe(32),
        ),
    )
    lines.extend(_build_storage_lines(answers=answers, real_values=True))
    return _join_env_lines(lines=lines)


def build_env_example_content(*, answers: SetupAnswers) -> str:
    lines = _build_base_env_lines(
        answers=answers,
        credentials=EnvCredentials(
            django_key="example-django-key",
            jwt_key="example-jwt-key-with-at-least-32-bytes",
            postgres_key="example-postgres-key",
            redis_key="example-redis-key",
        ),
    )
    lines.extend(_build_storage_lines(answers=answers, real_values=False))
    return _join_env_lines(lines=lines)


def build_test_env_example_content() -> str:
    return _join_env_lines(
        lines=[
            "# Test environment specific overrides",
            "ENVIRONMENT=test",
            "DJANGO_DEBUG=true",
            "DJANGO_SECRET_KEY=test-django-secret-key",
            "JWT_SECRET_KEY=test-jwt-secret-key-with-at-least-32-bytes",
            "LOGGING_LEVEL=DEBUG",
            "LOGFIRE_ENABLED=false",
            "DATABASE_TEST_NAME=test_db.sqlite3",
            "DATABASE_URL=sqlite:///test_db.sqlite3",
            "REDIS_URL=redis://localhost:6379/0",
            "",
            "STORAGE_BACKEND=local",
        ],
    )


def _build_base_env_lines(
    *,
    answers: SetupAnswers,
    credentials: EnvCredentials,
) -> list[str]:
    return [
        "COMPOSE_FILE=docker/docker-compose.yaml:docker/docker-compose.local.yaml",
        "",
        f"DJANGO_SECRET_KEY={credentials.django_key}",
        f"JWT_SECRET_KEY={credentials.jwt_key}",
        "",
        "ENVIRONMENT=local",
        "DJANGO_DEBUG=true",
        "LOGGING_LEVEL=DEBUG",
        f"LOGFIRE_SERVICE_NAME={answers.distribution_name}",
        "",
        'ALLOWED_HOSTS=["127.0.0.1", "localhost", "0.0.0.0"]',
        'CSRF_TRUSTED_ORIGINS=["http://localhost"]',
        "",
        "POSTGRES_USER=postgres",
        f"POSTGRES_DB={answers.package_name}",
        f"POSTGRES_PASSWORD={credentials.postgres_key}",
        'DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"',
        "",
        f"REDIS_PASSWORD={credentials.redis_key}",
        'REDIS_URL="redis://default:${REDIS_PASSWORD}@localhost:6379/0"',
        "",
    ]


def _build_storage_lines(*, answers: SetupAnswers, real_values: bool) -> list[str]:
    if answers.storage_mode == StorageMode.LOCAL:
        return ["STORAGE_BACKEND=local"]

    if answers.storage_mode == StorageMode.MINIO:
        return [
            "STORAGE_BACKEND=s3",
            "AWS_S3_ENDPOINT_URL=http://localhost:9000",
            "AWS_S3_PUBLIC_ENDPOINT_URL=http://localhost:9000",
            "AWS_S3_ACCESS_KEY_ID=example-minio-access-key-id",
            "AWS_S3_SECRET_ACCESS_KEY=example-minio-secret-access-key",
            "AWS_S3_REGION_NAME=us-east-1",
            "AWS_S3_PUBLIC_BUCKET_NAME=public",
            "AWS_S3_PROTECTED_BUCKET_NAME=protected",
        ]

    if real_values:
        return [
            "STORAGE_BACKEND=s3",
            f"AWS_S3_ENDPOINT_URL={answers.s3_endpoint_url or ''}",
            f"AWS_S3_PUBLIC_ENDPOINT_URL={answers.s3_public_endpoint_url or ''}",
            f"AWS_S3_ACCESS_KEY_ID={answers.s3_access_key_id or ''}",
            f"AWS_S3_SECRET_ACCESS_KEY={answers.s3_secret_access_key or ''}",
            f"AWS_S3_REGION_NAME={answers.s3_region_name or ''}",
            f"AWS_S3_PUBLIC_BUCKET_NAME={answers.s3_public_bucket_name}",
            f"AWS_S3_PROTECTED_BUCKET_NAME={answers.s3_protected_bucket_name}",
        ]

    return [
        "STORAGE_BACKEND=s3",
        "AWS_S3_ENDPOINT_URL=https://s3.example.com",
        "AWS_S3_PUBLIC_ENDPOINT_URL=https://cdn.example.com",
        "AWS_S3_ACCESS_KEY_ID=replace-me",
        "AWS_S3_SECRET_ACCESS_KEY=replace-me",
        "AWS_S3_REGION_NAME=us-east-1",
        "AWS_S3_PUBLIC_BUCKET_NAME=public",
        "AWS_S3_PROTECTED_BUCKET_NAME=protected",
    ]


def _join_env_lines(*, lines: list[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"
