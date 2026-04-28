from management.setup_wizard.prompts import (
    _ask_docs_site_url,
    _validate_distribution_name,
    _validate_package_name,
    _validate_project_name,
)


def test_project_name_validation_rejects_empty_and_template_names() -> None:
    assert _validate_project_name("") == "Project name is required."
    assert _validate_project_name("Fast Django") == (
        "Replace the template project name with your own project name."
    )
    assert _validate_project_name("Acme API") is True


def test_package_name_validation_rejects_template_name() -> None:
    assert _validate_package_name("fastdjango") == (
        "Replace the template package name with your own package name."
    )
    assert _validate_package_name("acme_api") is True


def test_distribution_name_validation_rejects_template_name() -> None:
    assert _validate_distribution_name("fastdjango") == (
        "Replace the template distribution name with your own distribution name."
    )
    assert _validate_distribution_name("acme-api") is True


def test_docs_site_url_prompt_is_skipped_when_docs_are_removed() -> None:
    assert _ask_docs_site_url(keep_docs=False) is None
