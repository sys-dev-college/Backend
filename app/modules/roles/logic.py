import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups.models import Group
from app.modules.roles.models import Role
from app.modules.users.models import UserGroupRoom


async def get_all_roles(session: AsyncSession):
    query = select(Role)
    res = await session.execute(query)
    return res.scalars().all()


async def get_role_by_user_and_room(session: AsyncSession, user_id: uuid.UUID, room_id: uuid.UUID):
    role = await session.scalar(
        select(Role)
        .join(Group, Group.role_id == Role.id)
        .join(
            UserGroupRoom,
            and_(
                UserGroupRoom.group_id == Group.id,
                UserGroupRoom.room_id == room_id,
                UserGroupRoom.user_id == user_id,
            ),
        )
    )
    return role
