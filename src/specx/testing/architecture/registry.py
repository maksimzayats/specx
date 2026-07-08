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
    ) -> tuple[ArchitectureRuleType, ...]:
        disabled = {str(rule_id) for rule_id in disabled_rules}
        return tuple(rule for rule in self.rules if str(rule().id) not in disabled)


def _validate_rules(rules: tuple[ArchitectureRuleType, ...]) -> None:
    seen: dict[str, ArchitectureRuleType] = {}
    for rule in rules:
        rule_id = str(rule().id)
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
