from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.users import logic, schemas
from app.modules.users.models import TokenBlacklist, User
from app.utils.dependencies import get_current_user, get_session
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
    # DO NOT REMOVE THIS CODE !!!
    # if user.is_accepted_agreement is False:
    #     return JSONResponse(
    #         content={"success": False, "message": "Ошибка регистрации. Соглашение не принято"},
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #     )
    user_exists = await User.get_user_by_email(session, user.email)
    if user_exists is not None:
        raise HTTPException(
            status_code=400,
            detail={"status": "False", "message": "Email already registered"},
        )
    # result = await logic.check_invite_expiration_time_of_user_and_create_user_object(
    #     session=session,
    #     user=user,
    # )
    # return result


@user_router.post("/login/", response_model=schemas.Token)
async def login(
    credentials: schemas.AuthCredentials,
    session: AsyncSession = Depends(get_session),
):
    user = await logic.authenticate_user(session, credentials.email, credentials.password)
    if not isinstance(user, User):
        raise HTTPException(status_code=400, detail=user)
    access_token = await logic.create_access_token(user)
    refresh_token = await logic.create_refresh_token(user)
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
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    data = current_user.to_dict()

    return data


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


@user_router.get("/register/accept/")
async def user_activate_view(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    user = await logic.user_activate_logic(
        session=session,
        user_id=user_id,
    )
    access_token = await logic.create_access_token(user)
    refresh_token = await logic.create_refresh_token(user)
    return {"access_token": access_token, "refresh_token": refresh_token}


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
    return DefaultResponse(success=True, message="Password restored")
