import unicodedata
from dataclasses import dataclass

from fastapi_template.core.user.dtos.create_user import CreateUserDTO
from fastapi_template.foundation.service import BaseService


@dataclass(kw_only=True)
class UserIdentityService(BaseService):
    """Normalize user identity fields before validation or lookup."""

    def normalize_create_user_data(self, *, data: CreateUserDTO) -> CreateUserDTO:
        """Normalize identity fields while preserving creation policy flags.

        Returns:
            A user creation DTO with normalized username and email.
        """
        return CreateUserDTO(
            username=self.normalize_username(username=data.username),
            email=self.normalize_email(email=str(data.email)),
            first_name=data.first_name,
            last_name=data.last_name,
            password=data.password,
            is_active=data.is_active,
            is_staff=data.is_staff,
            is_superuser=data.is_superuser,
        )

    def normalize_username(self, *, username: str) -> str:
        """Trim and Unicode-normalize a username for stable comparisons.

        Returns:
            Username normalized with NFKC.
        """
        return unicodedata.normalize("NFKC", username.strip())

    def normalize_email(self, *, email: str) -> str:
        """Trim an email address and case-fold only the domain part.

        Returns:
            Email address normalized for account uniqueness checks.
        """
        local_part, separator, domain = email.strip().partition("@")
        if not separator:
            return email.strip()

        return f"{local_part}@{domain.casefold()}"
