from functools import partial
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.background import BackgroundTask, BackgroundTasks

from app.middlewares.request_logging import logging_system


class RequestProcessingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        handler = super().get_route_handler()

        return partial(self.custom_route_handler, handler=handler)

    @classmethod
    async def custom_route_handler(cls, request: Request, handler) -> Response:
        await cls.check_access(request)
        response = await handler(request)
        if request.method == "OPTIONS":
            return response

        if request.headers.get("Content-Type") == "application/json":
            await request.json()

        if response.background is None:
            response.background = BackgroundTasks()
        elif isinstance(response.background, BackgroundTask):
            task = response.background
            response.background = BackgroundTasks()
            response.background.add_task(task)
        response.background.add_task(logging_system, request, response)

        return response

    @classmethod
    async def check_access(cls, request: Request):
        ...
        # request_headers = request.headers.items()
        # jwt_token = dict(request_headers).get("authorization")
        # if jwt_token is None:
        #     raise HTTPException(status_code=401, detail="Unauthorized")
        # token = jwt_token.split(" ")[1]
        # email = decode_access_token(token)
        # if email is None:
        #     raise HTTPException(status_code=401, detail="No user found")
        # url_path = request.url.path
        # async with SessionManager() as session:
        #     user = await User.get_user_by_email(session, email)
        #     roles = await _extract_roles_by_user(user, session)
        #     is_access_granted = await check_role_access(session, roles, url_path)

        #     if not is_access_granted:
        #         raise HTTPException(status_code=403, detail="Wrong role")
