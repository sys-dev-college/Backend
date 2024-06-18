import base64
import re
import uuid
from os import path
from typing import Optional
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.roles.models import Role
from app.modules.users import logic, schemas
from app.modules.users.models import TokenBlacklist, User
from app.modules.users.schemas import UserParamIn, UserParamList, UserParamOut, UserRetrieve
from app.utils.dependencies import get_current_user, get_log_context, get_session
from app.utils.response_helper import DefaultResponse

user_router = APIRouter(
    tags=["Users"],
    prefix="/api/users",
    route_class=RequestProcessingRoute,
)


@user_router.post("/register/")
async def register_user(
        user: schemas.UserBase,
        session: AsyncSession = Depends(get_session),
):
    user_exists = await User.get_user_by_email(session, user.email)
    if user_exists is not None:
        raise HTTPException(
            status_code=400,
            detail={"status": "False", "message": "Email already registered"},
        )
    result = await logic.register_user(
        session=session,
        user=user,
    )
    return result


@user_router.post("/login/", response_model=schemas.Token)
async def login(
        credentials: schemas.AuthCredentials,
        session: AsyncSession = Depends(get_session),
        log_context: dict = Depends(get_log_context),
):
    user = await logic.authenticate_user(session, credentials.email, credentials.password)
    if not isinstance(user, User):
        raise HTTPException(status_code=400, detail=user)
    access_token = await logic.create_access_token(user)
    refresh_token = await logic.create_refresh_token(user)
    log_context.update(
        {
            "details": {
                "email": credentials.email,
            }
        }
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


@user_router.post("/user-exists/")
async def user_exists(
        data: schemas.UserExists,
        session: AsyncSession = Depends(get_session),
):
    if await User.get_user_by_email(session, data.email):
        return schemas.UserExistsOut(user_exists=True)
    return schemas.UserExistsOut(user_exists=False)


@user_router.get("/me/")
async def get_me(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    data = current_user.to_dict()
    role_name = await session.scalar(select(Role).where(Role.id == current_user.role_id))
    data["role_name"] = role_name

    return data


@user_router.get("/{user_id}/")
async def get_user_by_id(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
):
    result = await logic.get_user_by_id(session=session, user_id=user_id)
    return UserRetrieve.model_validate(result)


@user_router.put("/me/")
async def update_user_data(
        user_data: schemas.UserUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    await logic.update_user_data(session, current_user.id, user_data)
    return DefaultResponse(success=True, status_code=200)


@user_router.post("/logout/")
async def logout(
        request: Request,
        session: AsyncSession = Depends(get_session),
):
    auth = request.headers["Authorization"]
    _, token = auth.split()
    await TokenBlacklist.add_tokens_to_blacklist(
        session=session,
        access_token=token,
    )
    return DefaultResponse(success=True, message="Successfully logged out")


@user_router.post("/fingerprint/")
async def create_user_fingerprint_view(
        browser_data: str = Form(),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    result = await logic.create_user_fingerprint_logic(
        browser_data=browser_data,
        session=session,
        user_id=current_user.id,
    )
    return result


@user_router.get("/register/accept/{user_id}/")
async def user_activate_view(
        user_id: UUID,
        session: AsyncSession = Depends(get_session),
):
    await logic.user_activate_logic(
        session=session,
        user_id=user_id,
    )
    response: str = ""

    parent_dir = path.dirname(path.abspath(__file__))
    async with (aiofiles.open(path.join(parent_dir, 'res', 'register_success.html'), "r+", encoding="utf-8")
                as response_file):
        response = await response_file.read()

    return HTMLResponse(content=response, status_code=200)


@user_router.post("/send-restore/")
async def send_restore_password_email_view(
        email_data: schemas.EmailRestorePassword,
        session: AsyncSession = Depends(get_session),
):
    user = await User.get_user_by_email(session, email_data.email)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail={"status": False, "message": "User not found"},
        )
    await logic.send_restore_password_email_logic(
        email=email_data.email,
        user_id=user.id,
    )
    return DefaultResponse(success=True, message="Email was sent")


@user_router.get("/restore-password/")
async def get_restore_static(
        user: str = Query(...),
):
    user_id = base64.b64decode(user).decode("utf-8")
    regex_find_user_id = re.compile(r"user_id: null")
    parent_dir = path.dirname(path.abspath(__file__))
    async with aiofiles.open(
            path.join(parent_dir, 'res', 'reset_password.html'),
            "r+",
            encoding="utf-8"
    ) as file:
        response = await file.read()
        response = regex_find_user_id.sub(f"user_id: \"{user_id}\"", response)

    return HTMLResponse(content=response, status_code=200)


@user_router.post("/restore/")
async def restore_password_view(
        restore_data: schemas.RestorePassword,
        session: AsyncSession = Depends(get_session),
):
    user = (await session.execute(select(User).where(User.id == restore_data.user_id))).scalar()
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"status": False, "message": "User not found"},
        )
    await logic.restore_password_logic(
        session=session,
        restore_data=restore_data,
    )
    return DefaultResponse(success=True, message="Password restored", status_code=200)


@user_router.post("/param/")
async def insert_param(
        user_param: UserParamIn,
        user_id: Optional[UUID] = Body(None),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    user = current_user
    if user_id:
        user_result = await session.scalar(select(User).where(User.id == user_id))
        if not user_result:
            return DefaultResponse(
                success=False,
                status_code=400,
                message="User doesn't exist"
            )
        user = user_result
    user_param_instance = await logic.create_user_param_instance(
        session=session,
        user_param=user_param,
        user=user,
    )
    return UserParamOut.model_validate(user_param_instance)


@user_router.get("/param/")
async def get_user_params(
        user_id: Optional[UUID] = Body(None),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    user = current_user
    if user_id:
        user_result = await session.scalar(select(User).where(User.id == user_id))
        if not user_result:
            return DefaultResponse(
                success=False,
                status_code=400,
                message="User doesn't exist"
            )
        user = user_result
    user_param_instances = await logic.get_user_param_instances(session=session, user=user)
    return UserParamList.model_validate(user_param_instances)
