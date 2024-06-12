from __future__ import annotations

import json
import typing

from fastapi.responses import Response

from app.utils.json_encoder_mixin import JSONEncoderMixin

if typing.TYPE_CHECKING:
    from starlette.background import BackgroundTask


class DefaultResponse(Response):

    """
    Helps compose strict format for response
    """

    media_type = "application/json"

    def __init__(
        self,
        message: typing.Any = None,
        success: bool | None = None,
        status_code: int = 200,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        media_type: typing.Optional[str] = None,
        background: typing.Optional[BackgroundTask] = None,
    ) -> None:
        content = {}
        if message:
            content.update({"message": message})

        if success is not None:
            content.update({"success": success})

        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=JSONEncoderMixin,
        ).encode("utf-8")
