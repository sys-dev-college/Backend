from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
)

from app.database.session import SessionManager
from app.modules.users.models import TokenBlacklist, User
from app.utils.jwt_utils import decode_access_token


class CodeAuthenticationError(AuthenticationError):
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code


class OAuth2Backend(AuthenticationBackend):
    @staticmethod
    def handle_error(_request: Request, exc: Exception):
        message = getattr(exc, "message", "Internal server error")
        code = getattr(exc, "code", 500)
        return JSONResponse(
            content={"detail": message},
            status_code=code,
        )

    async def authenticate(self, request: Request):  # type: ignore
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        scheme, token = auth.split()
        if scheme.lower() != "bearer":
            msg = "Invalid authentication scheme"
            raise CodeAuthenticationError(msg, code=401)
        email = decode_access_token(token)
        if not email:
            msg = "Invalid access token"
            raise CodeAuthenticationError(msg, code=401)
        async with SessionManager() as session:
            token_blacklist = await TokenBlacklist.is_token_blacklisted(
                session=session,
                token=token,
            )
            if token_blacklist is True:
                msg = "Access token has been revoked"
                raise CodeAuthenticationError(msg, code=401)
            user = await User.get_user_by_email(session, email)
            if user is None:
                msg = "User not found"
                raise CodeAuthenticationError(msg, code=401)
        request.state.user = user
        return AuthCredentials(["authenticated"]), user
