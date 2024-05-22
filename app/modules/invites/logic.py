
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.invites.models import Invite


async def update_or_get_invite_object_logic(session: AsyncSession, email: str):
    existing_invite = select(Invite).where(Invite.email == email)
    result = (await session.execute(existing_invite)).scalar()
    if result is not None:
        update_object = delete(Invite).where(Invite.email == email)
        await session.execute(update_object)
    return email
