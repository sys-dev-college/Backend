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
