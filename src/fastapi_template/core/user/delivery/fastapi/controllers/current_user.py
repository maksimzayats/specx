from dataclasses import dataclass, field
from http import HTTPStatus

from diwire import Injected
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from fastapi_template.core.authentication.delivery.fastapi.auth.authenticated_request import (
    AuthenticatedRequest,
)
from fastapi_template.core.authentication.delivery.fastapi.auth.jwt_auth_factory import (
    JWTAuthFactory,
)
from fastapi_template.core.user.delivery.fastapi.schemas.user import UserSchema
from fastapi_template.core.user.use_cases.get_active_user_by_id import (
    GetActiveUserByIdUseCase,
)
from fastapi_template.foundation.delivery.controller import BaseAsyncController


@dataclass(kw_only=True)
class CurrentUserController(BaseAsyncController):
    """Define CurrentUserController."""

    _jwt_auth_factory: Injected[JWTAuthFactory]
    _get_active_user_by_id_use_case: Injected[GetActiveUserByIdUseCase]

    _jwt_auth: HTTPBearer = field(init=False)

    def __post_init__(self) -> None:
        """Run post init."""
        self._jwt_auth = self._jwt_auth_factory()
        super().__post_init__()

    def register(self, registry: APIRouter) -> None:
        """Run register."""
        registry.add_api_route(
            path="/api/v1/users/me",
            endpoint=self.get_current_user,
            methods=["GET"],
            dependencies=[Depends(self._jwt_auth)],
            response_model=UserSchema,
        )

    async def get_current_user(self, request: AuthenticatedRequest) -> UserSchema:
        """Run get current user.

        Returns:
        The operation result.
        """
        user = await self._get_active_user_by_id_use_case.execute(
            user_id=request.state.user_id,
        )
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="User not found",
            )

        return UserSchema.model_validate(user, from_attributes=True)
