from dataclasses import dataclass
from secrets import choice
from string import ascii_letters, digits
from typing import ClassVar

from specx.core.foundation.capability import BaseCapability


@dataclass(kw_only=True, slots=True)
class RandomShortCodeCapability(BaseCapability):
    """Capability that generates random URL-safe short codes.

    Example:
        code = RandomShortCodeCapability().generate()
    """

    _alphabet: ClassVar[str] = ascii_letters + digits
    _length: ClassVar[int] = 7

    def generate(self) -> str:
        return "".join(choice(self._alphabet) for _ in range(self._length))
