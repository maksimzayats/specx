from http import HTTPStatus

from fastapi import HTTPException

AUTHENTICATE_HEADER = "WWW-Authenticate"
BEARER_AUTH_SCHEME = "Bearer"


def bearer_authentication_error(*, detail: str) -> HTTPException:
    """Build a bearer-authentication HTTP error.

    Returns:
        An HTTP 401 error with the bearer challenge header.
    """
    return HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail=detail,
        headers={AUTHENTICATE_HEADER: BEARER_AUTH_SCHEME},
    )
