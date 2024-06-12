from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import ErrorTypes, UserErrors


async def save_user_error_log_to_table(
    user_id: UUID,
    type_of_error: str,
    session: AsyncSession,
):
    error_object = await session.scalar(
        select(ErrorTypes).where(ErrorTypes.error_text == type_of_error)
    )
    if not error_object:
        msg = "Error type not found"
        raise ValueError(msg)
    session_data = UserErrors(
        user_id=user_id,
        error_type_id=error_object.error_type_id,
    )
    session.add(session_data)
    await session.commit()
