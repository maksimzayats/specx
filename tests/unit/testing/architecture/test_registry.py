from __future__ import annotations

from inspect import getdoc

import pytest

from specx.testing.architecture import (
    ArchitectureContext,
    BaseRule,
    SpecxArchitectureViolation,
    SpecxRuleId,
    SpecxRuleRegistryError,
)
from specx.testing.architecture.registry import SpecxRuleRegistry
from specx.testing.architecture.rules import BUILT_IN_RULES


class DuplicateCoreRule(BaseRule[SpecxRuleId, ArchitectureContext, SpecxArchitectureViolation]):
    """Duplicate rule used to prove registry IDs remain unique."""

    id = BUILT_IN_RULES[0]().id

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        return ()


def test_registry_rejects_duplicate_rule_ids() -> None:
    with pytest.raises(SpecxRuleRegistryError, match="duplicate architecture rule id"):
        SpecxRuleRegistry.build(extra_rules=(DuplicateCoreRule,))


def test_every_builtin_rule_has_useful_docstring() -> None:
    missing = [
        rule.__name__
        for rule in BUILT_IN_RULES
        if (docstring := getdoc(rule)) is None or len(docstring.split()) < 8
    ]

    assert missing == []


def test_builtin_rule_ids_are_unique() -> None:
    rule_ids = [str(rule().id) for rule in BUILT_IN_RULES]

    assert len(rule_ids) == len(set(rule_ids))


def test_every_builtin_rule_has_selection_metadata() -> None:
    metadata = [rule.metadata() for rule in BUILT_IN_RULES]

    assert all(item.family in {"neutral", "fastapi"} for item in metadata)
    assert all(item.summary for item in metadata)
    assert {str(item.rule_id) for item in metadata if not item.default_enabled} == {
        str(SpecxRuleId.FASTAPI_ROOT_AGENTS_MD_DOCUMENTS_DELIVERY),
        str(SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS),
    }


def test_all_selector_enables_every_builtin_rule() -> None:
    registry = SpecxRuleRegistry.build()

    enabled = registry.enabled_rules(
        disabled_rules=frozenset(),
        select=frozenset({"ALL"}),
    )

    assert enabled == BUILT_IN_RULES


def test_explicit_empty_select_disables_default_rules() -> None:
    registry = SpecxRuleRegistry.build()

    enabled = registry.enabled_rules(
        disabled_rules=frozenset(),
        select=frozenset(),
    )

    assert enabled == ()
