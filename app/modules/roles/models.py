import uuid
from typing import List, Optional

from sqlalchemy import ARRAY, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column()
    permissions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    # groups: Mapped[List["Group"]] = relationship(
    #     "Group",
    #     # secondary="group_roles_m2m",
    #     back_populates="role",
    #     lazy="noload",
    # )
    # url_permissions: Mapped[List["PermissionsToUrls"]] = relationship(
    #     "PermissionsToUrls",
    #     secondary="permissions_to_urls_m2m_role",
    #     back_populates="roles",
    #     lazy="noload",
    # )

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


# class PermissionsToUrlsM2MRole(Base):
#     __tablename__ = "permissions_to_urls_m2m_role"
#
#     role_id: Mapped[uuid.UUID] = mapped_column(
#         ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
#         primary_key=True,
#     )
#     permission_to_url_id: Mapped[uuid.UUID] = mapped_column(
#         ForeignKey("permissions_to_urls.id", ondelete="CASCADE", onupdate="CASCADE"),
#         primary_key=True,
#     )
#
#
# class PermissionsToUrls(Base):
#     __tablename__ = "permissions_to_urls"
#
#     id: Mapped[uuid.UUID] = mapped_column(
#         primary_key=True,
#         default=uuid.uuid4,
#     )
#     url: Mapped[str] = mapped_column()
#     permissions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
#     roles: Mapped[List["Role"]] = relationship(
#         "Role",
#         secondary="permissions_to_urls_m2m_role",
#         back_populates="url_permissions",
#         lazy="noload",
#     )
