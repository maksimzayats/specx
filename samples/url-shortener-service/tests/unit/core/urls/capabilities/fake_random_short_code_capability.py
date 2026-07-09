from __future__ import annotations

from dataclasses import dataclass, field

from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)


@dataclass(kw_only=True, slots=True)
class SequencedShortCodeCapability(RandomShortCodeCapability):
    """Deterministic short-code capability for URL unit tests.

    Example:
        capability = SequencedShortCodeCapability(codes=["abc1234"])
    """

    codes: list[str] = field(default_factory=list)
    generated_codes: list[str] = field(default_factory=list)

    def generate(self) -> str:
        if not self.codes:
            raise AssertionError("SequencedShortCodeCapability ran out of configured codes")

        code = self.codes.pop(0)
        self.generated_codes.append(code)

        return code
