from __future__ import annotations

from pathlib import Path

import pytest

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    assert_specx_architecture,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_ROOT = PROJECT_ROOT / "samples" / "task-db-service"


@pytest.mark.parametrize("rule_id", tuple(SpecxRuleId), ids=str)
def test_each_builtin_rule_accepts_sample_service(rule_id: SpecxRuleId) -> None:
    disabled_rules = frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)

    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=SAMPLE_ROOT,
            package_name="task_db_service",
            disabled_rules=disabled_rules,
        )
    )


def test_strict_architecture_accepts_sample_service() -> None:
    assert_specx_architecture(
        SpecxArchitectureConfig(
            project_root=SAMPLE_ROOT,
            package_name="task_db_service",
        )
    )
