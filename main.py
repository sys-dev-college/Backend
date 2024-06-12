from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from app.config import settings
from app.middlewares.content_length import RequestSizeLimitMiddleware
from app.middlewares.database_session import UniversalDBSessionMiddleware
from app.middlewares.get_current_user import OAuth2Backend
from app.modules.logs.views import log_router
from app.modules.notifications.views import notification_router
from app.modules.user_sessions.views import websocket_rout
from app.modules.users.views import user_router
from app.utils.websocket_manager import websocket_manager

middlewares = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(
        RequestSizeLimitMiddleware,
        max_request_size=settings.MAX_CONTENT_LENGTH,
        include_limits_in_error_responses=settings.LOGLEVEL == "DEBUG",
    ),
    Middleware(
        AuthenticationMiddleware,
        backend=OAuth2Backend(),
        on_error=OAuth2Backend.handle_error,
    ),
    Middleware(UniversalDBSessionMiddleware),
]


# API Endpoints
routes = [
    user_router,
    log_router,
    websocket_rout,
    notification_router,
]


@asynccontextmanager
async def lifespan(_app: FastAPI):

    app.state.websocket_manager = websocket_manager
    yield


def create_app():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        middleware=middlewares,
        lifespan=lifespan,
        debug=settings.LOGLEVEL == "DEBUG",
    )
    for route in routes:
        app.include_router(route)
    return app


app = create_app()

