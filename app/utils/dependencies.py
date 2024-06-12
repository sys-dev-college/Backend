import functools
from typing import Any, AsyncIterable, Callable, Optional, TypeVar

from fastapi import File, HTTPException, Request, params
from fastapi.requests import HTTPConnection
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import ParamSpec

from app.modules.users.models import User
from app.utils.websocket_manager import WebSocketManager


async def get_session(request: HTTPConnection) -> AsyncIterable[AsyncSession]:
    if "db_session" not in request.scope:
        msg = "Database session is not initialized"
        raise ValueError(msg)
    return request.scope["db_session"]


async def get_current_user(request: Request) -> User:
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )
    return request.state.user


async def get_websocket_manager(request: HTTPConnection) -> WebSocketManager:
    if not hasattr(request.app.state, "websocket_manager"):
        raise HTTPException(
            status_code=500,
            detail="Websocket manager is not initialized",
        )
    return request.app.state.websocket_manager


async def get_log_context(request: Request):
    if not hasattr(request.state, "log_context"):
        request.state.log_context = {
            "details": {},
        }
    return request.state.log_context


def generate_request_context(request: Request):
    return {"request": request}


P = ParamSpec("P")
T = TypeVar("T")


def copy_callable_signature(
        source: Callable[P, T],
) -> Callable[[Callable[..., T]], Callable[P, T]]:
    def wrapper(target: Callable[..., T]) -> Callable[P, T]:
        @functools.wraps(source)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            return target(*args, **kwargs)

        return wrapped

    return wrapper


class _RestrictedFile(params.File):
    max_content_length: Optional[int]

    @copy_callable_signature(params.File.__init__)
    def __init__(self, *args, **kwargs):
        self.max_content_length = kwargs.pop("max_content_length")
        super().__init__(*args, **kwargs)


@copy_callable_signature(File)
def RestrictedFile(  # noqa: N802
        *args: Callable[..., Any],
        max_content_length: Optional[int] = None,
        **kwargs: Callable[..., Any],
) -> Any:
    return _RestrictedFile(*args, max_content_length=max_content_length, **kwargs)
