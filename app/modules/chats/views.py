import uuid

from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.chats.logic import (
    add_new_user_in_chat,
    create_chat_instance,
    get_chat_by_id,
    get_chats_by_room_id,
    get_messages_by_chat_id,
)
from app.modules.chats.schemas import CreateChatSchema
from app.modules.users.models import User
from app.utils.dependencies import get_current_user, get_session, get_websocket_manager

chat_router = APIRouter(
    tags=["Chats"],
    prefix="/api/chats",
    route_class=RequestProcessingRoute,
)


@chat_router.post("/")
async def create_chat(
    chat_data: CreateChatSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    websocket_manager=Depends(get_websocket_manager),
):
    return await create_chat_instance(
        session=session,
        current_user=current_user,
        chat_data=chat_data,
        websocket_manager=websocket_manager,
    )


@chat_router.get("/message/")
async def get_messages_from_chat(
    chat_id: uuid.UUID = Query(),
    session: AsyncSession = Depends(get_session),
):
    return await get_messages_by_chat_id(session=session, chat_id=chat_id)


@chat_router.get("/")
async def list_chat_by_room(
    room_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_chats_by_room_id(session=session, room_id=room_id, current_user=current_user)


@chat_router.post("/user/")
async def add_user_in_chat(
    user_id: uuid.UUID = Form(),
    chat_id: uuid.UUID = Form(),
    session: AsyncSession = Depends(get_session),
):
    return await add_new_user_in_chat(session=session, user_id=user_id, chat_id=chat_id)


@chat_router.get("/{chat_id}/")
async def retrieve_chat(
    chat_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    return await get_chat_by_id(session=session, chat_id=chat_id)
