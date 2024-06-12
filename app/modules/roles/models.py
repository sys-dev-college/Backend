import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column()

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
    )

    @classmethod
    async def get_role_by_name(
        cls,
        session: AsyncSession,
        role_name: str,
    ):
        permissions = select(Role).where(Role.name == role_name)
        result = await session.execute(permissions)
        result = result.scalar()
        return result
