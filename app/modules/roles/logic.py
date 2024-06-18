import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.models import Role


async def get_all_roles(session: AsyncSession):
    query = select(Role)
    res = await session.execute(query)
    return res.scalars().all()


async def get_role_by_name(session: AsyncSession, name: str):
    role = await session.scalar(select(Role).where(Role.name == name))
    if not role:
        return None
    return role


async def get_role_by_id(session: AsyncSession, role_id: uuid.UUID):
    role = await session.scalar(select(Role).where(Role.id == role_id))
    if not role:
        return None
    return role
