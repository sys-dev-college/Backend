import json
from typing import Any, Dict, Optional

from fastapi import Request, Response, status
from sqlalchemy import select

from app.database.session import SessionManager
from app.modules.logs.models import Logs
from app.modules.user_sessions.models import Session
from app.utils.info_from_ws_session import get_addition_session_details
from app.utils.logging import logger


async def create_user_log(
    action_type,
    action_name,
    account,
    room_id,
    entity_id,
    document_name,
    ws_session: Optional[Session] = None,
    details: Optional[Dict[str, Any]] = None,
):
    async with SessionManager() as session:
        details_addons = await get_addition_session_details(session=session, ws_session=ws_session)

        if not details:
            details = {}

        details.update(details_addons)

        log_data = {
            "type": action_type,
            "name": action_name,
            "user_id": account,
            "room_id": room_id,
            "details": details,
        }

        log_instance = Logs(**log_data)
        log_instance.session_id = ws_session.id if ws_session else None

        session.add(log_instance)


async def get_websocket_session(request: Request) -> Optional[Session]:
    user_id = request.state.user.id
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
    "/api/rooms/+create": "Добавление комнаты",
    # "/api/rooms/+view": "Получение комнаты",
    "/api/rooms/+update": "Обновление настроек комнаты",
    "/api/rooms/+nda_enable": "Включение NDA для комнаты",
    "/api/rooms/+nda_disable": "Выключение NDA для комнаты",
    # "/api/rooms/agreement/+view": "Получение соглашения на комнату",
    # "/api/users/me/+update": "Обновление данных о пользователе",
    # "/api/users/me/+view": "Получение данных о пользователе",
    # "/api/documents/+view": "Получение списка документов",
    "/api/organizations/+create": "Создание организации",
    "/api/organizations/+delete": "Удаление организации",
    "/api/organizations/upload/+create": "Загрузка файлов организации",
    # "/api/documents/+delete": "Удаление документа",
    "/api/documents/+delete_confident": "Удаление конфиденциального документа",
    "/api/documents/permissions/+update": "Изменение прав на файл",
    "/api/groups/create/+create": "Создание группы",
    "/api/documents/confident/+view": "Получение файла дополнительного соглашения к документу",
    "/api/documents/confident/+delete": "Удаление файла дополнительного соглашения к документу",
    "/api/documents/confident/+create": "Добавление файла дополнительного соглашения к документу",
    "/api/documents/download/+view": "Просмотр документа",
    "/api/documents/download/+download": "Скачивание документа",
    "/api/documents/download/+download_confident": "Скачивание конфиденциального документа",
    "/api/documents/upload/+create": "Загрузка документа",
    "/api/documents/upload/+create_confident": "Загрузка конфиденциального документа",
    "/api/invites/invite/+create": "Создание приглашения",
    "/api/folders/permissions/+update": "Изменение прав на папку",
    "/api/invites/invite/data/+view": "Получение данных из инвайта",
    "/api/invites/invite/data/+room_invite": "Приглашение в комнату",
    "/api/notes/+create": "Создание заметки",
    "/api/folders/+create": "Создание папки",
    # "/api/folders/+delete": "Удаление папки",
    "/api/groups/+delete": "Удаление группы",
    # "/api/users/register/+create": "Регистрация пользователя",
    # "/api/users/login/+create": "Авторизация пользователя",
    "/api/users/me/+update": "Обновление данных пользователя",
    "/api/invites/invite/data+view": "Переход по приглашению",
    "/api/organizations/+update": "Обновление организации",
    "/api/groups/add_user/+create": "Добавление пользователя в группу",
    "/api/groups/add_user/+update": "Изменение группы пользователя",
    "/api/documents/agreement/+update": "Согласование документа",
    "/api/documents/agreement/decline/+update": "Отклонение cогласования документа",
    "/api/users/status/+update": "Согласование NDA",
    "/api/agreement/+create": "Запрос согласования документа",
    "/api/temp_links/+create": "Создание временной ссылки на документ",
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
    room_id = request.query_params.get("id") or log_context.get("room_id")
    entity_id = request.query_params.get("entity") or log_context.get("entity_id")
    document_name = request.query_params.get("document_name") or log_context.get("document_name")
    action_name = ROUTES_MAPPING.get(f"{request.url.path}+{action_type}")
    if action_name is None:
        return

    details = await extract_details(request, log_context)

    try:
        ws_session = await get_websocket_session(request)
    except ValueError:
        logger.warning("WS session not found, unable to log action")
        return

    await create_user_log(
        action_type=action_type,
        action_name=action_name,
        account=request.user.id if hasattr(request, "user") else None,
        room_id=room_id,
        entity_id=entity_id,
        details=details,
        ws_session=ws_session,
        document_name=document_name,
    )
