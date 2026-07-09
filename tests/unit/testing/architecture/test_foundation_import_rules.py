from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_foundation_import_rule_accepts_scoped_foundation_imports(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "dtos" / "task_dto.py",
        "from specx.core.foundation.dto import BaseDTO\n\n"
        "class TaskDTO(BaseDTO):\n"
        '    """DTO for task results.\n\n'
        "    Example:\n"
        "        TaskDTO()\n"
        '    """\n',
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.FOUNDATION_IMPORTS_USE_SCOPED_PACKAGES),
        )
    )

    assert report.violations == ()


def test_foundation_import_rule_rejects_removed_foundation_namespace(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "dtos" / "task_dto.py",
        "from specx.foundation.dto import BaseDTO\n\n"
        "class TaskDTO(BaseDTO):\n"
        '    """DTO for task results.\n\n'
        "    Example:\n"
        "        TaskDTO()\n"
        '    """\n',
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.FOUNDATION_IMPORTS_USE_SCOPED_PACKAGES),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (
            SpecxRuleId.FOUNDATION_IMPORTS_USE_SCOPED_PACKAGES,
            "imports specx.foundation.dto",
        )
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
