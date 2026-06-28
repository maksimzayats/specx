from typing import Any

from starlette.datastructures import State


class AuthenticatedRequestState(State):
    """Define AuthenticatedRequestState."""

    jwt_payload: dict[str, Any]
    user_id: int
