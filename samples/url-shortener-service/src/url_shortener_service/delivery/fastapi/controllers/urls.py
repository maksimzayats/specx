from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from specx.delivery.foundation.controller import BaseController

from url_shortener_service.core.urls.exceptions.invalid_target_url_value_error import (
    InvalidTargetUrlValueError,
)
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)
from url_shortener_service.core.urls.use_cases.get_short_url import (
    GetShortUrlQuery,
    GetShortUrlUseCase,
)
from url_shortener_service.core.urls.use_cases.resolve_short_url import (
    ResolveShortUrlQuery,
    ResolveShortUrlUseCase,
)
from url_shortener_service.delivery.fastapi.schemas.url_schema import (
    CreateShortUrlRequestSchema,
    ShortUrlResponseSchema,
)


@dataclass(kw_only=True, slots=True)
class UrlsController(BaseController[APIRouter]):
    """FastAPI controller that registers short URL routes.

    Example:
        UrlsController(
            _create_short_url_use_case=create_short_url,
            _get_short_url_use_case=get_short_url,
            _resolve_short_url_use_case=resolve_short_url,
        ).register(router)
    """

    _create_short_url_use_case: Injected[CreateShortUrlUseCase]
    _get_short_url_use_case: Injected[GetShortUrlUseCase]
    _resolve_short_url_use_case: Injected[ResolveShortUrlUseCase]

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/api/v1/short-urls",
            endpoint=self.create_short_url,
            methods=["POST"],
            response_model=ShortUrlResponseSchema,
            status_code=status.HTTP_201_CREATED,
        )
        registry.add_api_route(
            path="/api/v1/short-urls/{code}",
            endpoint=self.get_short_url,
            methods=["GET"],
            response_model=ShortUrlResponseSchema,
        )
        registry.add_api_route(
            path="/api/v1/r/{code}",
            endpoint=self.resolve_short_url,
            methods=["GET"],
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    async def create_short_url(
        self,
        request: CreateShortUrlRequestSchema,
    ) -> ShortUrlResponseSchema:
        try:
            result = await self._create_short_url_use_case.execute(
                command=CreateShortUrlCommand(target_url=request.target_url),
            )
        except InvalidTargetUrlValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"target_url": error.target_url, "message": "Target URL must be http(s)."},
            ) from error
        except ShortCodeCollisionError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "max_attempts": error.max_attempts,
                    "message": "Could not allocate a short code.",
                },
            ) from error

        return ShortUrlResponseSchema.model_validate(result)

    async def get_short_url(self, code: str) -> ShortUrlResponseSchema:
        try:
            result = await self._get_short_url_use_case.execute(
                query=GetShortUrlQuery(code=code),
            )
        except ShortUrlNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": error.code, "message": "Short URL not found"},
            ) from error

        return ShortUrlResponseSchema.model_validate(result)

    async def resolve_short_url(self, code: str) -> RedirectResponse:
        try:
            result = await self._resolve_short_url_use_case.execute(
                query=ResolveShortUrlQuery(code=code),
            )
        except ShortUrlNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": error.code, "message": "Short URL not found"},
            ) from error

        return RedirectResponse(
            url=result.target_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
