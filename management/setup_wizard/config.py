from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence
from io import StringIO
from typing import Any, cast

import tomlkit
from ruamel.yaml import YAML

from management.setup_wizard.models import SetupAnswers, StorageMode
from management.setup_wizard.text_rewrite import ProjectReferences, replace_project_references

SETUP_DEPENDENCIES = [
    "libcst>=1.8.6",
    "questionary>=2.1.1",
    "rich>=14.2.0",
    "ruamel.yaml>=0.18.16",
    "tomlkit>=0.13.3",
]


def update_pyproject_toml(
    content: str,
    *,
    answers: SetupAnswers,
    old_package_name: str,
) -> str:
    document = cast(Any, tomlkit.parse(content))
    cast(Any, document["project"])["name"] = answers.distribution_name

    _update_dependency_groups(document=document, answers=answers)
    _update_mypy_config(
        document=document,
        package_name=answers.package_name,
        old_package_name=old_package_name,
    )
    _update_coverage_config(
        document=document,
        package_name=answers.package_name,
        old_package_name=old_package_name,
    )
    return tomlkit.dumps(document)


def update_ruff_toml(content: str, *, package_name: str) -> str:
    document = cast(Any, tomlkit.parse(content))
    document["src"] = ["src", "management", "tests"]
    cast(Any, document["lint"]["isort"])["known-first-party"] = [package_name]
    return tomlkit.dumps(document)


def update_prek_toml(content: str) -> str:
    document = cast(Any, tomlkit.parse(content))
    for repo in cast(list[Any], document["repos"]):
        for hook in cast(list[Any], repo.get("hooks", [])):
            _update_prek_hook(hook=hook)

    return tomlkit.dumps(document)


def update_docker_compose_yaml(
    content: str,
    *,
    answers: SetupAnswers,
    old_package_name: str,
    is_local_overlay: bool,
) -> str:
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(content)
    _rewrite_yaml_strings(
        value=data,
        answers=answers,
        old_package_name=old_package_name,
    )

    if answers.storage_mode == StorageMode.MINIO:
        _configure_minio_compose(data=data, is_local_overlay=is_local_overlay)
    else:
        _remove_minio_compose(data=data)

    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def update_mkdocs_yaml(content: str, *, answers: SetupAnswers, old_package_name: str) -> str:
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(content)
    _rewrite_yaml_strings(
        value=data,
        answers=answers,
        old_package_name=old_package_name,
    )
    data["site_name"] = answers.project_name
    if answers.docs_site_url is not None:
        data["site_url"] = answers.docs_site_url.rstrip("/")
    else:
        data.pop("site_url", None)

    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def _update_dependency_groups(*, document: Any, answers: SetupAnswers) -> None:
    if "dependency-groups" not in document:
        document["dependency-groups"] = tomlkit.table()

    groups = document["dependency-groups"]
    if answers.keep_docs:
        groups.setdefault("docs", ["mkdocs>=1.6.1", "mkdocs-material>=9.6.0"])
    else:
        groups.pop("docs", None)

    if answers.delete_wizard:
        groups.pop("setup", None)
        return

    setup_dependencies = tomlkit.array()
    setup_dependencies.multiline(True)  # noqa: FBT003
    for dependency in SETUP_DEPENDENCIES:
        setup_dependencies.append(dependency)
    groups["setup"] = setup_dependencies


def _update_mypy_config(
    *,
    document: Any,
    package_name: str,
    old_package_name: str,
) -> None:
    tool_config = document["tool"]
    tool_config["django-stubs"]["django_settings_module"] = (
        f"{package_name}.infrastructure.django.settings"
    )
    for override in cast(list[Any], tool_config["mypy"].get("overrides", [])):
        module = override.get("module")
        if isinstance(module, str):
            override["module"] = module.replace(old_package_name, package_name)


def _update_coverage_config(
    *,
    document: Any,
    package_name: str,
    old_package_name: str,
) -> None:
    coverage_run = document["tool"]["coverage"]["run"]
    omit_values = [
        _rewrite_config_path(
            value=value,
            package_name=package_name,
            old_package_name=old_package_name,
        )
        for value in cast(list[str], coverage_run.get("omit", []))
    ]
    omit_values = [value for value in omit_values if value != f"src/{package_name}/manage.py"]
    if "management/manage.py" not in omit_values:
        omit_values.insert(0, "management/manage.py")
    coverage_run["omit"] = omit_values


def _rewrite_config_path(*, value: str, package_name: str, old_package_name: str) -> str:
    if value == f"src/{old_package_name}/manage.py":
        return "management/manage.py"

    return value.replace(f"src/{old_package_name}", f"src/{package_name}")


def _update_prek_hook(*, hook: Any) -> None:
    entry = hook.get("entry")
    if isinstance(entry, str) and "mypy src/ tests/" in entry:
        hook["entry"] = entry.replace("mypy src/ tests/", "mypy src/ management/ tests/")

    files = hook.get("files")
    if isinstance(files, str):
        hook["files"] = files.replace("^(src|tests)", "^(src|management|tests)")


def _rewrite_yaml_strings(
    *,
    value: Any,
    answers: SetupAnswers,
    old_package_name: str,
) -> None:
    if isinstance(value, MutableMapping):
        for key, child_value in value.items():
            if isinstance(child_value, str):
                value[key] = _rewrite_yaml_string(
                    text=child_value,
                    answers=answers,
                    old_package_name=old_package_name,
                )
            else:
                _rewrite_yaml_strings(
                    value=child_value,
                    answers=answers,
                    old_package_name=old_package_name,
                )
        return

    if isinstance(value, MutableSequence):
        for index, child_value in enumerate(value):
            if isinstance(child_value, str):
                value[index] = _rewrite_yaml_string(
                    text=child_value,
                    answers=answers,
                    old_package_name=old_package_name,
                )
            else:
                _rewrite_yaml_strings(
                    value=child_value,
                    answers=answers,
                    old_package_name=old_package_name,
                )


def _rewrite_yaml_string(*, text: str, answers: SetupAnswers, old_package_name: str) -> str:
    return replace_project_references(
        text=text,
        references=ProjectReferences(
            old_package_name=old_package_name,
            new_package_name=answers.package_name,
            project_name=answers.project_name,
            docs_site_url=answers.docs_site_url,
        ),
    )


def _configure_minio_compose(*, data: Any, is_local_overlay: bool) -> None:
    if is_local_overlay:
        return

    common_environment = data.get("x-common", {}).get("environment", {})
    common_environment["AWS_S3_ENDPOINT_URL"] = "http://minio:9000"


def _remove_minio_compose(*, data: Any) -> None:
    services = data.get("services", {})
    services.pop("minio", None)
    services.pop("minio-create-buckets", None)

    collectstatic_dependencies = services.get("collectstatic", {}).get("depends_on", {})
    collectstatic_dependencies.pop("minio-create-buckets", None)

    common_environment = data.get("x-common", {}).get("environment", {})
    common_environment.pop("AWS_S3_ENDPOINT_URL", None)

    volumes = data.get("volumes", {})
    volumes.pop("minio_data", None)
