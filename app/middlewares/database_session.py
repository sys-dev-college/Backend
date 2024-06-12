from starlette.types import ASGIApp, Receive, Scope, Send

from app.database.session import AsyncSessionMaker


class DBSessionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            session = scope.get("db_session")
            if not session:
                await send(message)
                return

            if message.get("type") == "http.response.start":
                if message["status"] // 200 != 1:
                    await session.rollback()
                else:
                    await session.commit()

            await send(message)
            return

        try:
            async with AsyncSessionMaker() as session:
                scope["db_session"] = session
                await self.app(scope, receive, send_wrapper)
        except Exception:
            session = scope.get("db_session")
            if session:
                await session.rollback()
            raise


class WebSocketDBSessionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async with AsyncSessionMaker() as session:
            try:
                scope["db_session"] = session
                await self.app(scope, receive, send)
            except Exception:
                session = scope.get("db_session")
                if session:
                    await session.rollback()
                raise
            await session.commit()


class UniversalDBSessionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            middleware = WebSocketDBSessionMiddleware(self.app)
            await middleware(scope, receive, send)
        elif scope["type"] == "http":
            middleware = DBSessionMiddleware(self.app)
            await middleware(scope, receive, send)
        else:
            await self.app(scope, receive, send)
