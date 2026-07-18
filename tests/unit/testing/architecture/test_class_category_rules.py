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
        "from specx.core.foundation.enums import BaseStrEnum\n\n"
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


def test_explicit_base_rule_reports_class_location(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "policy.py",
        "class OrderPolicy:\n    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(
                SpecxRuleId.NON_FOUNDATION_SOURCE_CLASSES_HAVE_EXPLICIT_BASE_CLASSES
            ),
        )
    )

    assert [
        (violation.symbol, violation.line, violation.column) for violation in report.violations
    ] == [("OrderPolicy", 1, 1)]


def test_suffix_rule_reports_class_locations(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "policy.py",
        "class Mystery(object):\n    pass\n\nclass SystemTime(BaseClock):\n    pass\n",
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

    assert [
        (violation.symbol, violation.line, violation.column) for violation in report.violations
    ] == [
        ("Mystery", 1, 1),
        ("SystemTime", 4, 1),
    ]


def test_generic_base_service_rule_rejects_qualified_base(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "core" / "tasks" / "services" / "billing.py",
        "import specx.core.foundation as foundation\n\n"
        "class BillingService(foundation.BaseService):\n"
        "    pass\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            disabled_rules=_disable_all_except(SpecxRuleId.GENERIC_BASE_SERVICE_IS_NOT_USED),
        )
    )

    assert [
        (violation.message, violation.symbol, violation.line, violation.column)
        for violation in report.violations
    ] == [("inherits BaseService", "BillingService", 3, 1)]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
