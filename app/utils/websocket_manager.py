import asyncio
import json
import uuid
from datetime import datetime
from typing import ClassVar, Dict, List

from sqlalchemy import String, and_, null, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket

from app.database.session import SessionManager
from app.modules.user_sessions.models import Session
from app.modules.user_sessions.schemas import ChatMessageData, SessionMethod
from app.modules.users.models import User
from app.utils.logging import logger


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def close_all_connections(self):
        async with SessionManager() as session:
            for user_id in self.connections:
                await session.execute(
                    update(Session)
                    .where(and_(Session.user_id == user_id, Session.end_at.is_(null())))
                    .values(end_at=datetime.now())
                )
            self.connections.clear()

    def __del__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.close_all_connections())

    @staticmethod
    async def process_document_update(
        room_connections: Dict[str, WebSocket], document_id: uuid.UUID
    ):
        connections_to_broadcast: List[WebSocket] = list(room_connections.values())
        return {"document_id": str(document_id)}, connections_to_broadcast

    @staticmethod
    async def process_chat_message(
        room_connections: Dict[str, WebSocket],
        user_id: uuid.UUID,
        chat_id: uuid.UUID,
    ):
        connections_to_broadcast: List[WebSocket] = list(room_connections.values())

        async with SessionManager() as session:
            user = await session.scalar(select(User).where(User.id == user_id))
            notification_message = f"{user.user_name} новое сообщение в чате"
            # await create_notification_for_room_members_or_single_user(
            #     session=session,
            #     current_user_id=user_id,
            #     notification_message=notification_message,
            #     notification_type=NotificationType.ROOM_CHAT,
            #     send_for_single_user=True,
            # )
        return {
            "user_name": user.user_name,
            "email": user.email,
            "chat_id": chat_id,
        }, connections_to_broadcast

    async def init_session_state(self, session: AsyncSession, user_session, data):
        await session.refresh(user_session)
        user_session.state = data
        session.add(user_session)
        await session.commit()

    async def update_session_state(self, session: AsyncSession, user_session: Session, data: dict):
        await session.refresh(user_session)
        session_state = user_session.state
        session_state.update(**data)

        user_session.state = session_state
        session.add(user_session)
        await session.commit()

    async def init_chat_message(self, session: AsyncSession, user_session: Session, data: dict):
        serialized_data = ChatMessageData.model_validate(data)
        author_id = user_session.user_id

        await insert_message_in_chat(
            session=session, message_data=serialized_data, author_id=author_id
        )
        await self.broadcast(**serialized_data.model_dump(), event="chat", user_id=author_id)

    _BROADCAST_STRATEGY: ClassVar[dict] = {
        "document": process_document_update.__get__(object),
        "chat": process_chat_message.__get__(object),
    }

    _STATE_METHODS_STRATEGY: ClassVar[dict] = {
        SessionMethod.update: update_session_state,
        SessionMethod.init: init_session_state,
        SessionMethod.chat: init_chat_message,
    }

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        if self.connections.get(user_id):
            try:
                self.connections.pop(user_id)
            except Exception as error:
                logger.exception(
                    "An error occurred while disconnecting user %s: Error: %s", user_id, error
                )

    async def get_room_connections(self, room_id: str):
        async with (SessionManager() as session):
            user_sessions = (
                await session.scalars(
                    select(Session.user_id.cast(String)).where(
                        and_(
                            Session.state.op("->>")("room_id").cast(String) == room_id,
                            Session.end_at.is_(null()),
                        )
                    )
                )
            ).all()
            return {key: value for key, value in self.connections.items() if key in user_sessions}

    async def broadcast(self, message: str, room_id: str, event: str, **params):
        timestamp = datetime.now().isoformat()
        formatted_message = {
            "timestamp": timestamp,
            "message": message,
            "room_id": room_id,
            "event": event,
        }
        room_connections = await self.get_room_connections(room_id=room_id)
        if not room_connections:
            return
        processing_method = self._BROADCAST_STRATEGY.get(event)
        if not processing_method:
            return
        addons, connections_to_broadcast = await processing_method(
            room_connections=room_connections, **params
        )
        formatted_message.update(addons)
        for connection in connections_to_broadcast:
            await connection.send_text(json.dumps(formatted_message))

    async def process_method(self, session: AsyncSession, user_session: Session, message: dict):
        processing_method = self._STATE_METHODS_STRATEGY.get(message["type"])
        if not processing_method:
            return
        await processing_method(self, session, user_session, message["data"])


websocket_manager = WebSocketManager()
