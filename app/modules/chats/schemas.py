import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel

from app.modules.users.schemas import UserShort


class CreateChatSchema(BaseModel):
    room_id: uuid.UUID
    title: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    members_ids: Optional[List[uuid.UUID]] = None


class ChatFullSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    title: str
    archived: bool
    entity_id: Optional[uuid.UUID] = None
    created_at: datetime.datetime
    users: List[UserShort] = Field(serialization_alias="members")


class MessageOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    created_at: datetime.datetime
    author: UserShort


class ListMessageSchema(RootModel):
    root: List[MessageOutSchema]


class ListChatSchema(RootModel):
    root: List[ChatFullSchema]
