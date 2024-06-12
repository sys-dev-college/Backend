import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Enum,
    FetchedValue,
    ForeignKey,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    joinedload,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.functions import concat

from app.database.session import Base
from app.modules.logs.models import Logs
from app.modules.notifications.models import Notification
from app.modules.roles.models import Role
from app.utils.crud_model_mixin import ModelCRUDMixin

if TYPE_CHECKING:
    from app.modules.calendar.models import Calendar


class UserStatus(enum.IntEnum):
    WAITING_FOR_APPROVAL = 0
    ACTIVE = 1


class User(Base, ModelCRUDMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=FetchedValue(),
    )
    first_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    changed_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
    )
    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_avatar_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        default=None,
        server_default=FetchedValue()
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        default=None,
        server_default=FetchedValue(),
    )
    role: Mapped[Optional["Role"]] = relationship(
        Role,
        back_populates="users",
    )
    status: Mapped[Optional[UserStatus]] = mapped_column(
        Enum(UserStatus, native_enum=False),
        default=UserStatus.WAITING_FOR_APPROVAL,
    )
    notifications: Mapped[List["Notification"]] = relationship(
        Notification,
        back_populates="user",
    )
    logs: Mapped[List["Logs"]] = relationship(
        Logs,
        back_populates="user",
    )
    fingerprints: Mapped[List["UserFingerprint"]] = relationship(
        "UserFingerprint",
        back_populates="user",
        cascade="all",
    )
    user_errors: Mapped[List["UserErrors"]] = relationship(
        "UserErrors",
        back_populates="user",
        cascade="all",
    )
    calendars: Mapped[List["Calendar"]] = relationship(
        "Calendar",
        back_populates="user",
    )
    assigned_calendars: Mapped[List["Calendar"]] = relationship(
        "Calendar",
        back_populates="assigner",
    )
    user_params: Mapped[List["UserParam"]] = relationship(
        "UserParam",
        back_populates="user",
    )

    @property
    def is_authenticated(self) -> bool:
        return True

    @hybrid_property
    def user_name(self) -> str:  # type: ignore
        # First and last name can be None
        if self.first_name is None and self.last_name is None:
            return self.email
        return " ".join(filter(None, [self.first_name, self.last_name]))

    @user_name.expression
    @classmethod
    def user_name(cls):
        return concat(cls.first_name, " ", cls.last_name)

    @classmethod
    async def get_clients_by_trainer_id(
            cls,
            session: AsyncSession,
            trainer_id: uuid.UUID,
    ):
        user_stmt = (
            select(User)
            .where(User.trainer_id == trainer_id)
        )
        user_result = await session.scalars(user_stmt)
        result = user_result.unique().all()

        return result

    @classmethod
    async def get_user_by_email(
            cls,
            session: AsyncSession,
            email: str,
            relation_fields_names_to_load: Optional[List[str]] = None,
    ) -> Optional["User"]:
        user_stmt = select(User).where(User.email == email)
        if relation_fields_names_to_load is not None:
            load_objects = [
                joinedload(getattr(cls, name)) for name in relation_fields_names_to_load
            ]
            user_stmt = user_stmt.options(*load_objects)
        user_result = await session.execute(user_stmt)
        user = user_result.unique().one_or_none()
        if user is None:
            return None
        return user[0]


class TokenBlacklist(Base):
    __tablename__ = "user_token_blacklist"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    access_token: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )

    @classmethod
    async def add_tokens_to_blacklist(
            cls,
            session: AsyncSession,
            access_token: str,
    ):
        token_blacklist = cls(access_token=access_token)
        session.add(token_blacklist)

    @classmethod
    async def is_token_blacklisted(cls, session: AsyncSession, token: str):
        query = select(cls).where(cls.access_token == token)
        res = await session.execute(query)
        blacklisted_token = res.scalar_one_or_none()
        return blacklisted_token is not None


class UserFingerprint(Base, ModelCRUDMixin):
    __tablename__ = "user_fingerprint"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    user: Mapped["User"] = relationship("User", back_populates="fingerprints")
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
    )
    fingerprint_data: Mapped[dict] = mapped_column(JSON)


class ErrorTypes(Base):
    __tablename__ = "error_types"

    error_type_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    error_text: Mapped[str] = mapped_column(nullable=False)
    note: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_errors: Mapped[List["UserErrors"]] = relationship(
        "UserErrors",
        back_populates="error_type",
        cascade="all",
    )


class UserErrors(Base):
    __tablename__ = "user_errors"

    error_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    user: Mapped["User"] = relationship("User", back_populates="user_errors")
    error_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("error_types.error_type_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    error_type: Mapped["ErrorTypes"] = relationship("ErrorTypes", back_populates="user_errors")


class UserParam(Base):
    __tablename__ = "user_params"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, server_default=FetchedValue())
    name: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=FetchedValue(),)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="user_params")
