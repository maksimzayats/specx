from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Generic, TypeVar

ContextT = TypeVar("ContextT")
ViolationT = TypeVar("ViolationT")
RuleIdT = TypeVar("RuleIdT", bound=StrEnum | str, covariant=True)


class BaseRule(ABC, Generic[RuleIdT, ContextT, ViolationT]):
    """Base for one architecture rule with a stable identifier and typed result."""

    id: RuleIdT

    @abstractmethod
    def check(self, context: ContextT) -> tuple[ViolationT, ...]:
        """Return every violation found by this rule for the supplied context."""
