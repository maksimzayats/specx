from datetime import datetime

from fastapi_template.foundation.dto import BaseDTO


class ReplaceRefreshSessionTokenDTO(BaseDTO):
    """Define ReplaceRefreshSessionTokenDTO."""

    expected_refresh_token_hash: str
    refresh_token_hash: str
    last_used_at: datetime
    expires_after: datetime
