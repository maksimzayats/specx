from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_agents_md_rule_accepts_non_sqlalchemy_project_without_migration_commands(
    tmp_path: Path,
) -> None:
    _write_minimal_project_guidance(tmp_path)

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.ROOT_AGENTS_MD_DOCUMENTS_PROJECT_COMMANDS_AND_BOUNDARIES
            ),
        )
    )

    assert report.violations == ()


def test_agents_md_rule_requires_migration_commands_for_alembic_project(
    tmp_path: Path,
) -> None:
    _write_minimal_project_guidance(tmp_path)
    _write(tmp_path / "alembic.ini", "[alembic]\n")

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.ROOT_AGENTS_MD_DOCUMENTS_PROJECT_COMMANDS_AND_BOUNDARIES
            ),
        )
    )

    assert len(report.violations) == 1
    assert "make migration-check" in report.violations[0].message
    assert "make makemigrations" in report.violations[0].message


def _write_minimal_project_guidance(project_root: Path) -> None:
    _write(
        project_root / "AGENTS.md",
        "# Agent Instructions\n\n"
        "- Package lives under `src/demo_service`\n"
        "- FastAPI entrypoint: `demo_service.delivery.fastapi.__main__:app`\n"
        "- make check\n"
        "- make lint\n"
        "- make test\n"
        "- BaseCapability\n"
        "- BaseGateway\n"
        "- BasePureService\n"
        "- BaseReadService\n"
        "- BaseEffectService\n"
        "- Use cases return DTOs, not entities\n"
        "- Query use cases must not call repository mutators\n",
    )
    _write(project_root / "Makefile", "check:\n\nlint:\n\ntest:\n")


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
