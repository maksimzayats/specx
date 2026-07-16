from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from inspect import getdoc
from typing import Generic, TypeVar

ContextT = TypeVar("ContextT")
ViolationT = TypeVar("ViolationT")
RuleIdT = TypeVar("RuleIdT", bound=StrEnum | str, covariant=True)


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecxRuleMetadata:
    """Metadata used to select and explain one architecture rule."""

    rule_id: StrEnum | str
    family: str
    summary: str
    default_enabled: bool
    required_project_surface: str | None


class BaseRule(ABC, Generic[RuleIdT, ContextT, ViolationT]):
    """Base for one architecture rule with a stable identifier and typed result."""

    id: RuleIdT
    family = "neutral"
    default_enabled = True
    required_project_surface: str | None = None

    @classmethod
    def metadata(cls) -> SpecxRuleMetadata:
        """Return stable selection and explanation metadata for this rule."""

        docstring = getdoc(cls) or cls.__name__
        return SpecxRuleMetadata(
            rule_id=cls.id,
            family=cls.family,
            summary=docstring.splitlines()[0],
            default_enabled=cls.default_enabled,
            required_project_surface=cls.required_project_surface,
        )

    @abstractmethod
    def check(self, context: ContextT) -> tuple[ViolationT, ...]:
        """Return every violation found by this rule for the supplied context."""
