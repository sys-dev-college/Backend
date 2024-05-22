import json
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_logging import create_user_log
from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.user_sessions.models import Session
from app.modules.user_sessions.schemas import MessageData
from app.modules.users.models import User, UserFingerprint
from app.utils.dependencies import get_session, get_websocket_manager
from app.utils.info_from_client_ip import IPInfo
from app.utils.logging import logger

websocket_rout = APIRouter(
    tags=["Websocket"],
    prefix="/users",
    route_class=RequestProcessingRoute,
)


@websocket_rout.websocket("/{user_id}/")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session: AsyncSession = Depends(get_session),
    websocket_manager=Depends(get_websocket_manager),
):
    if not websocket.client:
        logger.error("Websocket client is not found")
        return
    client_ip = websocket.client.host
    client_location = await IPInfo.get_location(client_ip=client_ip)

    fingerprint_query = (
        select(UserFingerprint)
        .where(UserFingerprint.user_id == user_id)
        .order_by(UserFingerprint.updated_at.desc())
    )
    fingerprint: UserFingerprint = await session.scalar(fingerprint_query)

    # Field start_at must be identical to field updated_at in fingerprint (we initialize them around the same time)
    start_at = fingerprint.updated_at
    session_data = Session(
        user_id=user_id,
        fingerprint_id=fingerprint.id,
        ip=client_ip,
        location=client_location,
        start_at=start_at,
    )
    session.add(session_data)
    # TODO (aleksandr): We must use commit to make new session available for all workers
    await session.commit()
    user_object = await session.scalar(select(User).where(User.id == user_id))
    if user_object is None:
        logger.error(f"User with id {user_id} is not found")
        return
    if not user_object.first_name:
        logger.error(f"User with id {user_id} has not first name")
        return
    await create_user_log(
        action_type="create",
        action_name="Авторизация пользователя",
        account=user_id,
        room_id=None,
        entity_id=None,
        ws_session=session_data,
        document_name=None,
    )
    await websocket_manager.connect(user_id=user_id, websocket=websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data is not None:
                message = MessageData.model_validate(json.loads(data))
                await websocket_manager.process_method(
                    session, session_data, message.model_dump(exclude_unset=True)
                )
    except (WebSocketDisconnect, WebSocketException):
        end_at = datetime.now()
        session_data.end_at = end_at
        session.add(session_data)
        await websocket_manager.disconnect(user_id)
