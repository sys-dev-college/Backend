import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionMethod(enum.Enum):
    update = "update"
    init = "init"
    chat = "chat"


class ChatMessageData(BaseModel):
    message: str
    room_id: str
    chat_id: UUID
    created_at: datetime


class MessageData(BaseModel):
    type: SessionMethod
    data: dict
