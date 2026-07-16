from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_core_inner_import_rule_rejects_httpx2(tmp_path: Path) -> None:
    source_path = (
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py"
    )
    _write_httpx2_pure_service(source_path)

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.CORE_INNER_PACKAGES_DO_NOT_IMPORT_OUTER_LAYERS_OR_IO_LIBRARIES
            ),
        )
    )

    assert [(violation.message, violation.path) for violation in report.violations] == [
        ("imports httpx2", source_path)
    ]


def test_pure_service_rule_rejects_httpx2(tmp_path: Path) -> None:
    source_path = (
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "title_service.py"
    )
    _write_httpx2_pure_service(source_path)

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.PURE_SERVICES_DO_NOT_DEPEND_ON_IO_OR_RUNTIME_STATE
            ),
        )
    )

    assert [(violation.message, violation.path) for violation in report.violations] == [
        ("imports httpx2", source_path)
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write_httpx2_pure_service(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "import httpx2\n\n"
        "from specx.core.foundation.pure_service import BasePureService\n\n\n"
        "class TitleService(BasePureService):\n"
        "    pass\n",
        encoding="utf-8",
    )
