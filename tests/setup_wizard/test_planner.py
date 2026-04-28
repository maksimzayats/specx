from __future__ import annotations

import textwrap
import tomllib
from pathlib import Path
from typing import Any

from management.setup_wizard.models import SetupAnswers, StorageMode
from management.setup_wizard.planner import build_setup_plan


def test_full_package_rename_rewrites_imports_config_and_docs(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(
        project_name="Acme API",
        package_name="acme_api",
        distribution_name="acme-api",
        docs_site_url="https://docs.example.com",
        storage_mode=StorageMode.MINIO,
        delete_wizard=False,
    )

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    assert not (tmp_path / "src" / "fastdjango").exists()
    renamed_module = tmp_path / "src" / "acme_api" / "core" / "sample.py"
    assert "from acme_api.foundation.services import BaseService" in renamed_module.read_text()

    pyproject = _read_toml(tmp_path / "pyproject.toml")
    assert pyproject["project"]["name"] == "acme-api"
    assert pyproject["tool"]["django-stubs"]["django_settings_module"] == (
        "acme_api.infrastructure.django.settings"
    )

    ruff = _read_toml(tmp_path / "ruff.toml")
    assert ruff["lint"]["isort"]["known-first-party"] == ["acme_api"]

    docs_index = (tmp_path / "docs" / "en" / "index.md").read_text()
    assert "src/acme_api/core/sample.py" in docs_index
    assert "https://docs.example.com" in (tmp_path / "docs" / "mkdocs.yml").read_text()
    assert (tmp_path / "docs" / "en" / "CNAME").read_text() == "docs.example.com\n"


def test_blank_docs_site_url_keeps_docs_local_only(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(
        project_name="Acme API",
        package_name="acme_api",
        distribution_name="acme-api",
        docs_site_url=None,
        delete_wizard=False,
    )

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    assert "site_url" not in (tmp_path / "docs" / "mkdocs.yml").read_text()
    assert not (tmp_path / "docs" / "en" / "CNAME").exists()
    assert "[local docs](docs/en)" in (tmp_path / "README.md").read_text()


def test_local_storage_prunes_minio_compose_services(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(storage_mode=StorageMode.LOCAL, delete_wizard=False)

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    compose = (tmp_path / "docker" / "docker-compose.yaml").read_text()
    local_overlay = (tmp_path / "docker" / "docker-compose.local.yaml").read_text()

    assert "minio:" not in compose
    assert "minio-create-buckets" not in compose
    assert "minio_data" not in compose
    assert "AWS_S3_ENDPOINT_URL" not in compose
    assert "minio:" not in local_overlay


def test_remote_s3_writes_placeholders_to_examples_and_real_values_to_env(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(
        storage_mode=StorageMode.REMOTE_S3,
        delete_wizard=False,
        s3_endpoint_url="https://storage.example.com",
        s3_public_endpoint_url="https://assets.example.com",
        s3_region_name="eu-central-1",
        s3_access_key_id="real-access-key",
        s3_secret_access_key="real-secret-key",  # noqa: S106
    )

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    env_content = (tmp_path / ".env").read_text()
    env_example_content = (tmp_path / ".env.example").read_text()

    assert "AWS_S3_ENDPOINT_URL=https://storage.example.com" in env_content
    assert "AWS_S3_SECRET_ACCESS_KEY=real-secret-key" in env_content
    assert "AWS_S3_ENDPOINT_URL=https://s3.example.com" in env_example_content
    assert "real-secret-key" not in env_example_content


def test_docs_removal_deletes_docs_config_targets_and_links(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(keep_docs=False, delete_wizard=False)

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    assert not (tmp_path / "docs").exists()
    assert "docs" not in _read_toml(tmp_path / "pyproject.toml")["dependency-groups"]
    assert "docs:" not in (tmp_path / "Makefile").read_text()
    assert "## Documentation" not in (tmp_path / "README.md").read_text()


def test_self_delete_removes_wizard_files_and_setup_dependency_group(tmp_path: Path) -> None:
    _create_mini_repo(repo_root=tmp_path)
    answers = _answers(delete_wizard=True)

    build_setup_plan(repo_root=tmp_path, answers=answers).apply(run_commands=False)

    assert not (tmp_path / "management" / "setup_wizard").exists()
    assert not (tmp_path / "tests" / "setup_wizard").exists()
    assert "setup" not in _read_toml(tmp_path / "pyproject.toml")["dependency-groups"]
    assert "setup:" not in (tmp_path / "Makefile").read_text()


def _answers(
    *,
    project_name: str = "Example API",
    package_name: str = "example_api",
    distribution_name: str = "example-api",
    docs_site_url: str | None = None,
    storage_mode: StorageMode = StorageMode.LOCAL,
    keep_docs: bool = True,
    delete_wizard: bool = True,
    s3_endpoint_url: str | None = None,
    s3_public_endpoint_url: str | None = None,
    s3_region_name: str | None = None,
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
) -> SetupAnswers:
    return SetupAnswers(
        project_name=project_name,
        package_name=package_name,
        distribution_name=distribution_name,
        docs_site_url=docs_site_url,
        storage_mode=storage_mode,
        keep_docs=keep_docs,
        delete_wizard=delete_wizard,
        overwrite_env=True,
        s3_endpoint_url=s3_endpoint_url,
        s3_public_endpoint_url=s3_public_endpoint_url,
        s3_region_name=s3_region_name,
        s3_access_key_id=s3_access_key_id,
        s3_secret_access_key=s3_secret_access_key,
    )


def _create_mini_repo(*, repo_root: Path) -> None:
    _write(
        repo_root / "src" / "fastdjango" / "core" / "sample.py",
        """
        from fastdjango.foundation.services import BaseService

        MODULE_PATH = "src/fastdjango/core/sample.py"
        SETTINGS_MODULE = "fastdjango.infrastructure.django.settings"


        class SampleService(BaseService):
            pass
        """,
    )
    _write(repo_root / "src" / "fastdjango" / "__init__.py", "")
    _write(
        repo_root / "tests" / "sample_test.py",
        "from fastdjango.core.sample import SampleService\n",
    )
    _write(repo_root / "management" / "setup_wizard" / "__init__.py", "")
    _write(repo_root / "tests" / "setup_wizard" / "test_old.py", "")
    _write(
        repo_root / "README.md",
        "# Fast Django\n\n## Documentation\n\nFull documentation is available at [fastdjango.zayats.dev](https://fastdjango.zayats.dev).\n\n## Tech Stack\n",
    )
    _write(repo_root / "docs" / "mkdocs.yml", _mkdocs_content())
    _write(
        repo_root / "docs" / "en" / "index.md",
        "Use src/fastdjango/core/sample.py at https://fastdjango.zayats.dev\n",
    )
    _write(repo_root / "docs" / "en" / "CNAME", "fastdjango.zayats.dev\n")
    _write(repo_root / ".env.example", "STORAGE_BACKEND=s3\n")
    _write(repo_root / ".env.test.example", "STORAGE_BACKEND=s3\n")
    _write(repo_root / "pyproject.toml", _pyproject_content())
    _write(repo_root / "ruff.toml", _ruff_content())
    _write(repo_root / "prek.toml", _prek_content())
    _write(repo_root / "Makefile", _makefile_content())
    _write(repo_root / "docker" / "docker-compose.yaml", _compose_content())
    _write(repo_root / "docker" / "docker-compose.local.yaml", _compose_overlay_content())
    _write(repo_root / "docker" / "docker-compose.test.yaml", _compose_overlay_content())


def _pyproject_content() -> str:
    return textwrap.dedent(
        """
        [project]
        name = "fastdjango"
        version = "0.1.0"

        [dependency-groups]
        dev = ["pytest"]
        docs = ["mkdocs"]
        setup = ["questionary"]

        [tool.mypy]

        [[tool.mypy.overrides]]
        module = "fastdjango.*.migrations.*"
        disable_error_code = ["no-untyped-def"]

        [tool.django-stubs]
        django_settings_module = "fastdjango.infrastructure.django.settings"

        [tool.coverage.run]
        omit = [
            "src/fastdjango/manage.py",
            "src/fastdjango/infrastructure/django/settings.py",
        ]
        """,
    ).lstrip()


def _ruff_content() -> str:
    return textwrap.dedent(
        """
        src = ["src", "tests"]

        [lint]

        [lint.isort]
        known-first-party = ["fastdjango"]
        """,
    ).lstrip()


def _prek_content() -> str:
    return textwrap.dedent(
        """
        [[repos]]
        repo = "local"

        [[repos.hooks]]
        id = "ruff-check"
        name = "ruff check"
        entry = "uv run ruff check ."
        files = "^(src|tests)/.*\\\\.py$"
        pass_filenames = false

        [[repos.hooks]]
        id = "mypy"
        name = "mypy"
        entry = "uv run --env-file .env.test.example mypy src/ tests/"
        files = "^(src|tests)/.*\\\\.py$"
        pass_filenames = false
        """,
    ).lstrip()


def _makefile_content() -> str:
    return textwrap.dedent(
        """
        migrate:
        \tuv run src/fastdjango/manage.py migrate

        setup:
        \tuv run --group setup python -m management.setup_wizard $(ARGS)

        docs:
        \tuv run mkdocs serve --livereload -f docs/mkdocs.yml

        docs-build:
        \tuv run mkdocs build -f docs/mkdocs.yml

        .PHONY: migrate setup docs docs-build
        """,
    ).lstrip()


def _compose_content() -> str:
    return textwrap.dedent(
        """
        x-common:
          environment:
            AWS_S3_ENDPOINT_URL: "http://minio:9000"

        services:
          api:
            command:
              - fastdjango.entrypoints.fastapi.app:app
          migrations:
            command: python src/fastdjango/manage.py migrate --noinput
          collectstatic:
            command: python src/fastdjango/manage.py collectstatic --noinput
            depends_on:
              minio-create-buckets:
                condition: service_completed_successfully
          minio:
            image: minio/minio:latest
          minio-create-buckets:
            image: minio/mc

        volumes:
          minio_data:
            driver: local
        """,
    ).lstrip()


def _compose_overlay_content() -> str:
    return textwrap.dedent(
        """
        services:
          minio:
            ports:
              - "9000:9000"
        """,
    ).lstrip()


def _mkdocs_content() -> str:
    return textwrap.dedent(
        """
        site_name: Fast Django
        site_url: https://fastdjango.zayats.dev
        docs_dir: en
        """,
    ).lstrip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))
