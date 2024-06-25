from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ColumnElement, and_, desc, or_, select
from sqlalchemy.orm.strategy_options import joinedload

from app.modules.chats.models import Chat, ChatEntityType, Message, UserChat
from app.modules.chats.schemas import (
    CHAT_TITLES,
    ChatFullSchema,
    CreateChatSchema,
    ListChatSchema,
    ListMessageSchema,
)
from app.modules.users.models import User
from app.utils.response_helper import DefaultResponse

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.modules.user_sessions.schemas import ChatMessageData


async def get_chat_by_id(session: AsyncSession, chat_id: uuid.UUID) -> ChatFullSchema:
    chat = await session.scalar(
        select(Chat)
        .where(Chat.id == chat_id)
        .options(joinedload(Chat.room), joinedload(Chat.users))
    )

    return ChatFullSchema.model_validate(chat)


async def get_existed_chat(
    session: AsyncSession,
    *params: ColumnElement[bool],
):
    return await session.scalar(select(Chat).where(and_(*params)))


async def insert_message_in_chat(
    session: AsyncSession, message_data: ChatMessageData, author_id: uuid.UUID
):
    chat_message = Message(
        chat_id=message_data.chat_id,
        author_id=author_id,
        content=message_data.message,
        created_at=message_data.created_at,
    )

    session.add(chat_message)
    await session.commit()


async def get_chats_by_user_id(session: AsyncSession, user_id: uuid.UUID):
    return await session.scalars(
        select(Chat).join(UserChat, UserChat.chat_id == Chat.id).where(UserChat.user_id == user_id)
    )


async def create_chat_instance(
    session: AsyncSession,
    current_user: User,
    chat_data: CreateChatSchema,
    websocket_manager,
):
    chat_params = chat_data.model_dump()
    chat_members_ids = chat_params.pop("members_ids")
    chat_room_id = chat_params.pop("room_id")
    chat_entity_type = chat_params.get("entity_type")
    chat_title = CHAT_TITLES.get(chat_entity_type)
    title_part: Optional[str] = chat_data.title

    title = chat_title["title"].format(title_part)
    chat_params["title"] = title

    if not chat_members_ids and chat_entity_type == ChatEntityType.PRIVATE:
        return DefaultResponse(
            success=False,
            status_code=400,
            message="Field members_ids can't null without entity_type PRIVATE",
        )

    chat_instance = Chat(**chat_params)

    session.add(chat_instance)
    await session.commit()
    await session.refresh(chat_instance)

    await websocket_manager.broadcast(
        message="New chat was created",
        room_id=str(chat_room_id),
        event="new_chat",
        chat_id=chat_instance.id,
        user_id=current_user.id,
    )

    return ChatFullSchema.model_validate(chat_instance)


async def get_messages_by_chat_id(session: AsyncSession, chat_id: uuid.UUID):
    messages = await session.scalars(
        select(Message)
        .where(Message.chat_id == chat_id)
        .options(joinedload(Message.author))
        .order_by(desc(Message.created_at))
    )
    return ListMessageSchema.model_validate(messages.all())


async def get_chats_by_room_id(session: AsyncSession, room_id: uuid.UUID, current_user: User):
    # TODO (aleksandr): rewrite it in invite logic


    # user_in_room = await session.scalar(
    #     select(UserGroupRoom).where(
    #         and_(
    #             UserGroupRoom.room_id == room_id,
    #             UserGroupRoom.user_id == current_user.id,
    #         )
    #     )
    # )
    # if not user_in_room:
    #     return DefaultResponse(
    #         message="User is not in Room",
    #         success=False,
    #         status_code=400,
    #     )
    #
    chats = (
        (
            await session.scalars(
                select(Chat)
                .join(Message, Message.chat_id == Chat.id, isouter=True)
                .join(UserChat, UserChat.chat_id == Chat.id, isouter=True)
                .where(
                    or_(
                        UserChat.user_id == current_user.id,
                    )
                )
                .order_by(desc(Message.created_at))
                .options(
                    joinedload(Chat.users),
                )
            )
        )
        .unique()
        .all()
    )

    return ListChatSchema.model_validate(chats)


async def add_new_user_in_chat(session: AsyncSession, user_id: uuid.UUID, chat_id: uuid.UUID):
    user_in_chat = await session.scalar(
        select(UserChat).where(and_(UserChat.user_id == user_id, UserChat.chat_id == chat_id))
    )

    if user_in_chat:
        return DefaultResponse(
            status_code=400,
            message="User already in this chat",
            success=False,
        )

    new_user_chat_relation = UserChat(
        user_id=user_id,
        chat_id=chat_id,
    )

    session.add(new_user_chat_relation)
    await session.flush()

    chat = await session.scalar(
        select(Chat)
        .where(Chat.id == chat_id)
        .options(
            joinedload(Chat.users),
        )
    )

    return ChatFullSchema.model_validate(chat)
