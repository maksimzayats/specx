from __future__ import annotations

from dataclasses import dataclass
from inspect import getdoc

from specx._internal.exceptions import BaseSpecxError
from specx.testing.architecture.models import ArchitectureRuleType, RuleIdentifier
from specx.testing.architecture.rules import BUILT_IN_RULES


class SpecxRuleRegistryError(BaseSpecxError):
    """Raised when architecture rules cannot be registered safely."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecxRuleRegistry:
    """Validated collection of architecture rule classes to execute."""

    rules: tuple[ArchitectureRuleType, ...]

    @classmethod
    def build(
        cls,
        *,
        extra_rules: tuple[ArchitectureRuleType, ...] = (),
    ) -> SpecxRuleRegistry:
        rules = (*BUILT_IN_RULES, *extra_rules)
        _validate_rules(rules)
        return cls(rules=rules)

    def enabled_rules(
        self,
        *,
        disabled_rules: frozenset[RuleIdentifier],
        select: frozenset[str] | None = None,
        extend_select: frozenset[str] = frozenset(),
    ) -> tuple[ArchitectureRuleType, ...]:
        disabled = {str(rule_id) for rule_id in disabled_rules}
        rule_ids = {str(rule.metadata().rule_id) for rule in self.rules}
        families = {rule.metadata().family for rule in self.rules}
        unknown_disabled = disabled - rule_ids
        if unknown_disabled:
            raise SpecxRuleRegistryError(
                f"unknown disabled rule selectors: {sorted(unknown_disabled)}"
            )
        known_selectors = rule_ids | families | {"ALL"}
        selected = select or frozenset()
        unknown_selected = selected - known_selectors
        if unknown_selected:
            raise SpecxRuleRegistryError(f"unknown rule selectors: {sorted(unknown_selected)}")
        unknown_extended = extend_select - known_selectors
        if unknown_extended:
            raise SpecxRuleRegistryError(
                f"unknown extended rule selectors: {sorted(unknown_extended)}"
            )

        return tuple(
            rule
            for rule in self.rules
            if str(rule.metadata().rule_id) not in disabled
            and (
                (
                    rule.metadata().default_enabled
                    if select is None
                    else _selector_matches(rule, selectors=select)
                )
                or _selector_matches(rule, selectors=extend_select)
            )
        )


def _selector_matches(
    rule: ArchitectureRuleType,
    *,
    selectors: frozenset[str],
) -> bool:
    metadata = rule.metadata()
    return "ALL" in selectors or str(metadata.rule_id) in selectors or metadata.family in selectors


def _validate_rules(rules: tuple[ArchitectureRuleType, ...]) -> None:
    seen: dict[str, ArchitectureRuleType] = {}
    for rule in rules:
        metadata = rule.metadata()
        rule_id = str(metadata.rule_id)
        if rule_id in seen:
            raise SpecxRuleRegistryError(
                f"duplicate architecture rule id {rule_id!r} on "
                f"{seen[rule_id].__name__} and {rule.__name__}",
            )
        seen[rule_id] = rule

        docstring = getdoc(rule)
        if docstring is None or len(docstring.split()) < 8:
            raise SpecxRuleRegistryError(
                f"{rule.__name__} must have a useful class docstring",
            )
        if not metadata.family or not metadata.family.isidentifier():
            raise SpecxRuleRegistryError(
                f"{rule.__name__} must declare an identifier-safe rule family"
            )
        if metadata.required_project_surface is not None:
            surface = metadata.required_project_surface
            if surface.startswith("/") or ".." in surface.split("/"):
                raise SpecxRuleRegistryError(
                    f"{rule.__name__} must declare a relative required project surface"
                )
