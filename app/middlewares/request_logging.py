import json
from typing import Any, Dict, Optional

from fastapi import Request, Response, status
from sqlalchemy import select
from starlette.authentication import UnauthenticatedUser

from app.database.session import SessionManager
from app.modules.logs.models import Logs
from app.modules.user_sessions.models import Session
from app.utils.logging import logger


async def create_user_log(
    action_type,
    action_name,
    account,
    ws_session: Optional[Session] = None,
    details: Optional[Dict[str, Any]] = None,
):
    async with SessionManager() as session:
        # details_addons = await get_addition_session_details(session=session, ws_session=ws_session)

        if not details:
            details = {}

        # details.update(details_addons)

        log_data = {
            "type": action_type,
            "name": action_name,
            "user_id": account,
            "details": details,
        }

        log_instance = Logs(**log_data)
        log_instance.session_id = ws_session.id if ws_session else None

        session.add(log_instance)


async def get_websocket_session(request: Request) -> Optional[Session]:
    try:
        user_id = request.state.user.id
    except AttributeError:
        return None
    async with SessionManager() as session:
        if sid := request.app.state._state["websocket_manager"].connections.get(str(user_id)):
            user_session = request.app.state._state["websocket_manager"].user_sessions[sid]
            return user_session

        session_query = (
            select(Session).where(Session.user_id == user_id).order_by(Session.start_at.desc())
        )
        ws_session = await session.scalar(session_query)
        # TODO (aleksandr): Session can be None
        #
        # if ws_session is None:
        #     msg = "Session not found"
        #     raise ValueError(msg)

        return ws_session


ROUTES_MAPPING = {
    "/api/users/me/+view": "Получение данных о пользователе",
    "/api/invites/invite/+create": "Создание приглашения",
    "/api/invites/invite/data/+view": "Получение данных из инвайта",
    "/api/users/register/+create": "Регистрация пользователя",
    "/api/users/login/+create": "Авторизация пользователя",
    "/api/users/me/+update": "Обновление данных пользователя",
    "/api/invites/invite/data+view": "Переход по приглашению",
    "/api/calendars/+view": "Получение списка задач на день",
    "/api/tasks/+view": "Получение списка подзадач",
    "/api/tasks/+delete": "Удаление подзадачи",
    "/api/tasks/complete/+update": "Изменение статуса подзадачи",
    "/api/users/logout/+update": "Выход пользователя из системы",
}

LIST_OF_ROUTERS = (
    "rooms",
    "users",
    "documents",
    "invites",
    "folders",
    "notes",
    "organizations",
    "groups",
    "agreement",
    "temp_links",
)


def should_skip_logging(
    request: Request,
    response: Optional[Response],
    log_context: Dict[str, Any],
) -> bool:
    if response and response.status_code == status.HTTP_307_TEMPORARY_REDIRECT:
        return True
    path = request.url.path

    if path in ["docs", "openapi.json", "favicon.ico", ""]:
        return True

    if request.method not in ("GET", "PUT", "POST", "DELETE"):
        return True

    api_route = path.split("/")[2]
    if api_route not in LIST_OF_ROUTERS:
        return True

    if log_context.get("skip"):
        return True

    return False


async def extract_details(request: Request, log_context: Dict[str, Any]) -> Dict[str, Any]:
    details = log_context.get("details", {})
    if request.headers.get("Content-Type") == "application/json":
        body = await request.json()
        details.update(body.get("details", {}))
    if request._form:
        query_form: Optional[str] = request._form.get("details")  # type: ignore
        details.update(json.loads(query_form) if query_form else {})
    if request.query_params:
        query_details = request.query_params.get("details")
        details.update(json.loads(query_details) if query_details else {})

    return details


async def logging_system(request: Request, response: Optional[Response] = None):
    log_context = getattr(request.state, "log_context", {})
    if should_skip_logging(request, response, log_context):
        return

    action_type = request.query_params.get("action") or log_context.get("action_type")
    action_name = ROUTES_MAPPING.get(f"{request.url.path}+{action_type}")
    if action_name is None:
        return

    details = await extract_details(request, log_context)
    details["ip"] = request.client.host

    try:
        ws_session = await get_websocket_session(request)
    except ValueError:
        logger.warning("WS session not found, unable to log action")
        ws_session = None

    await create_user_log(
        action_type=action_type,
        action_name=action_name,
        account=request.user.id if hasattr(request, "user") and type(request.user) is not UnauthenticatedUser else None,
        details=details,
        ws_session=ws_session,
    )
