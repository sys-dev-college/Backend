from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from fastapi import HTTPException
from fastapi.requests import HTTPConnection

if TYPE_CHECKING:
    from fastapi.routing import APIRoute
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_MAX_REQUEST_SIZE = 2_621_440  # 2.5MB, same as Django (https://docs.djangoproject.com/en/1.11/ref/settings/#data-upload-max-memory-size)


class _TooLarge(HTTPException):
    # oh no :(
    msg: ClassVar[str]

    def __init__(self, limit_bytes: int | None) -> None:
        self.limit = limit_bytes
        detail = (
            self.msg + f" Max allowed size is {limit_bytes} bytes." if limit_bytes else self.msg
        )
        super().__init__(
            status_code=413,
            detail=detail,
        )


class ChunkTooLarge(_TooLarge):
    msg = "Chunk size is too large."


class RequestTooLarge(_TooLarge):
    msg = "Request body is too large."


class RequestSizeLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        max_request_size: int | None = DEFAULT_MAX_REQUEST_SIZE,
        max_chunk_size: int | None = None,
        include_limits_in_error_responses: bool = False,
    ) -> None:
        self.app = app
        self.max_content_length = max_request_size
        self.max_chunk_size = max_chunk_size
        self.include_limits_in_error_responses = include_limits_in_error_responses

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        total_size = 0

        async def rcv() -> Message:
            nonlocal total_size
            nonlocal scope

            message = await receive()
            if message["type"] == "http.disconnect":
                return message

            conn = HTTPConnection(scope)
            content_length = int(conn.headers.get("content-length", "0"))
            # at that point, we already have route matched, so we can check for parameters and if it's a file upload
            # we can use the max_request_size
            if not conn.scope.get("route"):
                return message

            route: APIRoute = conn.scope["route"]

            for param in route.dependant.body_params:
                if isinstance(param.field_info, _RestrictedFile):
                    max_content_length = param.field_info.max_content_length
                    break
            else:
                max_content_length = self.max_content_length

            if max_content_length is not None and content_length > max_content_length:
                msg = max_content_length if self.include_limits_in_error_responses else None
                raise RequestTooLarge(msg)

            chunk_size = len(message.get("body", b""))
            total_size += chunk_size

            if self.max_chunk_size is not None and chunk_size > self.max_chunk_size:
                msg = self.max_chunk_size if self.include_limits_in_error_responses else None
                raise ChunkTooLarge(msg)

            if max_content_length is not None and total_size > max_content_length:
                msg = max_content_length if self.include_limits_in_error_responses else None
                raise RequestTooLarge(msg)

            return message

        await self.app(scope, rcv, send)
