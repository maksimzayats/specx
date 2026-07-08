from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_suffix_rule_accepts_base_str_enum_category(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "infrastructure" / "environment_enum.py",
        "from specx.foundation.enums import BaseStrEnum\n\n"
        "class EnvironmentEnum(BaseStrEnum):\n"
        "    LOCAL = 'local'\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.CLASSES_USE_SUFFIX_FROM_MOST_SPECIFIC_FOUNDATION_CATEGORY
            ),
        )
    )

    assert report.violations == ()


def test_raw_common_base_rule_rejects_str_enum_outside_foundation(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "infrastructure" / "environment_enum.py",
        "from enum import StrEnum\n\nclass EnvironmentEnum(StrEnum):\n    LOCAL = 'local'\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.NON_FOUNDATION_CLASSES_DO_NOT_USE_RAW_COMMON_BASES
            ),
        )
    )

    violation_details = [
        (violation.rule_id, violation.message, violation.symbol) for violation in report.violations
    ]
    assert violation_details == [
        (
            SpecxRuleId.NON_FOUNDATION_CLASSES_DO_NOT_USE_RAW_COMMON_BASES,
            "uses ['StrEnum']",
            "EnvironmentEnum",
        )
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
