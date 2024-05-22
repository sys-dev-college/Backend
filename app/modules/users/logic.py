import base64
import json
import uuid
from datetime import datetime

from sqlalchemy import String, and_, cast, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.smpt_sender.sender import email_sender
from app.modules.users import schemas
from app.modules.users.models import User, UserFingerprint, UserStatus
from app.utils import jwt_utils
from app.utils.hashing import Hasher
from app.utils.save_user_error_log import save_user_error_log_to_table


async def create_access_token(user: User):
    return jwt_utils.create_access_token(data={"sub": user.email})


async def create_refresh_token(user: User):
    return jwt_utils.create_refresh_token(data={"sub": user.email})


async def create_user(session: AsyncSession, user_data: schemas.UserBase) -> User:
    hashed_password = Hasher.get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
    )
    session.add(user)
    await session.flush()
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str):
    user = await User.get_user_by_email(session, email)
    if not user:
        return "User not found"
    if user.status == UserStatus.WAITING_FOR_APPROVAL:
        await save_user_error_log_to_table(
            user_id=user.id,
            type_of_error="user_activate",
            session=session,
        )
        return "User is waiting for approval"
    if not Hasher.verify_password(password, user.hashed_password):
        await save_user_error_log_to_table(
            user_id=user.id,
            type_of_error="incorrect_password",
            session=session,
        )
        return "User password is incorrect"
    return user


async def update_user_data(
    session: AsyncSession,
    user_id: uuid.UUID,
    user_data: schemas.UserUpdate,
):
    queryset = (
        update(User)
        .where(User.id == user_id)
        .values(
            **user_data.model_dump(
                exclude_unset=True,
            ),
        )
    )
    await session.execute(queryset)


# # async def add_user_to_room_and_group(
#     session: AsyncSession,
#     user_id: uuid.UUID,
#     room_id: uuid.UUID,
#     group_id: Optional[uuid.UUID] = None,
# ):
    # if group_id:
    #     user_group = UserGroupRoom(
    #         user_id=user_id,
    #         group_id=group_id,
    #         room_id=room_id
    #     )
    #     session.add(user_group)
    # await create_user_group_room_object(
    #     session=session, room_id=room_id, user_id=user_id, group_id=group_id
    # )


# async def get_permission_data_from_user_filter_by_room_id(
#     user_id: uuid.UUID,
#     room_id: uuid.UUID,
#     session: AsyncSession,
# ):
#     user_permission = await User.get_user_permission_list_by_current_user_id(
#         session=session,
#         current_user_id=user_id,
#         room_id=room_id,
#     )
#     permission_room_entity = (
#         await Permission.get_permissions_type_by_permission_subject_entity_type(
#             session=session,
#             permission_subject_entity_type="room",
#         )
#     )
#     result_permissions = change_response_permission_for_user(
#         permission_room_entity, user_permission
#     )
#     return result_permissions


def change_response_permission_for_user(first_lst, second_lst):
    if second_lst is not None:
        result = {key: key in second_lst[0] for key in first_lst}
    else:
        result = {key: False for key in first_lst}
    return result



async def create_user_fingerprint_logic(
    browser_data: str,
    session: AsyncSession,
    user_id: uuid.UUID,
):
    fingerprint_json = json.loads(browser_data)

    # To compare two json we need present them as JSON and convert to varchar type
    user_fingerprint = await session.scalar(
        select(UserFingerprint).where(
            and_(
                cast(UserFingerprint.fingerprint_data.as_json(), String)
                == cast(json.dumps(fingerprint_json), String),
                UserFingerprint.user_id == user_id,
            )
        )
    )

    if user_fingerprint:
        finger_id = user_fingerprint.id
        update_object = (
            update(UserFingerprint)
            .where(UserFingerprint.id == finger_id)
            .values(updated_at=datetime.now())
            .returning(UserFingerprint)
        )
        update_data = await session.execute(update_object)
        return update_data.scalar()
    fingerprint = UserFingerprint(
        user_id=user_id,
        fingerprint_data=json.loads(browser_data),
    )
    session.add(fingerprint)
    return fingerprint


# async def check_invite_expiration_time_of_user_and_create_user_object(
#     session: AsyncSession,
#     user: schemas.UserBase,
# ):
    # queryset = select(Invite.created_at).where(Invite.email == user.email)
    # invite_result = (await session.execute(queryset)).scalar()
    # current_time = datetime.now()
    # if invite_result is not None:
    #     time_difference = current_time - invite_result

        # if time_difference > timedelta(hours=72):
        #     return JSONResponse(
        #         content={
        #             "message": "Invite has expired",
        #             "success": False,
        #         },
        #         status_code=400,
        #     )

    # user_data = await create_user(session, user)
    # link = f"{settings.INVITE_PROTOCOL}://{settings.INVITE_DOMAIN}/users/register/accept/{user_data.id}"
    # await email_sender(
    #     email=user.email,
    #     subject="Подтверждение регистрации",
    #     body_text=f"""
    #         \nУважаемый {user.email},
    #         \nДля завершения регистрации в системе It-Fits перейдите по ссылке: {link}
    #         \nС уважением, команда It-Fits
    #         """,
    #     body_type="text",
    # )
    # if user.invite_type == "master":
    #     create_room_data = RoomCreate()  # type: ignore
    #     await create_room(session, create_room_data, user_data)
    # elif user.room_id is not None:
    #     await add_user_to_room_and_group(
    #         session,
    #         user_data.id,
    #         user.room_id,
    #         user.group_id,
    #     )
    # return {
    #     "status": "True",
    #     "data": schemas.UserOut(
    #         id=user_data.id,
    #         email=user_data.email,
    #     ),
    # }


# async def get_users_by_room_id_and_group_id(
#     session,
#     room_id: uuid.UUID,
#     group_id: uuid.UUID,
# ):
#     queryset = select(User).join(
#         UserGroupRoom,
#         and_(
#             UserGroupRoom.user_id == User.id,
#             UserGroupRoom.room_id == room_id,
#             UserGroupRoom.group_id == group_id,
#         ),
#     )
#     result = await session.execute(queryset)
#     return result.scalars().all()


async def user_activate_logic(
    session: AsyncSession,
    user_id: uuid.UUID,
):
    user = (await session.execute(select(User).where(User.id == user_id))).scalar()
    if not user:
        return {"status": "False", "message": "User not found"}
    queryset = (
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.ACTIVE,
        )
    )
    await session.execute(queryset)
    return user


async def send_restore_password_email_logic(
    email: str,
    user_id: uuid.UUID,
):
    encoded_user_id = base64.b64encode(str(user_id).encode("utf-8")).decode()
    link = f"{settings.INVITE_PROTOCOL}://{settings.INVITE_DOMAIN}/users/restore-password/user={encoded_user_id}"
    await email_sender(
        email=email,
        subject="Восстановление пароля",
        body_text=f"""
            \nЗдравствуйте,
            \nчтобы восстановить пароль в Athena.VDR перейдите по ссылке: {link}
            \nЕсли Вы не запрашивали восстановление пароля для входа на сайт: Athena.VDR {settings.INVITE_PROTOCOL}://{settings.INVITE_DOMAIN}/login игнорируйте данное письмо.
            \nС уважением, команда Athena.VDR
            """,
        body_type="text",
    )


async def restore_password_logic(
    restore_data: schemas.RestorePassword,
    session: AsyncSession,
):
    hashed_password = Hasher.get_password_hash(restore_data.password)
    await User.update_attributes_by_conditions(
        session=session,
        filters={"id": restore_data.user_id},
        attributes_vs_values={"hashed_password": hashed_password},
    )
