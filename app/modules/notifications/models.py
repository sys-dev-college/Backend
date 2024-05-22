import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import JSON, Enum, FetchedValue, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class NotificationType(enum.Enum):
    INVITE = "invite"
    ADD_NOTE = "add_note"
    CHANGE_STATUS = "change_status"
    AGREEMENT_INITIATED = "agreement_initiated"
    UPLOAD_DOCUMENT = "upload_document"
    NDA_ENABLE = "nda_enable"
    UPDATE_USER_PERMISSIONS = "update_user_permissions"
    ROOM_CHAT = "room_chat"


class NotificationStatus(enum.Enum):
    NEW = 0
    VIEWED = 1


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            native_enum=False,
        )
    )
    message: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(
            NotificationStatus,
            native_enum=False,
        )
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="notifications")
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )

    @staticmethod
    async def add_notification_for_existing_user(
        session: AsyncSession,
        user_id: UUID,
        message: str,
        notification_type: NotificationType,
        details: Optional[dict] = None,
    ):
        notification_instance = Notification(
            type=notification_type,
            status=NotificationStatus.NEW,
            message=message,
            user_id=user_id,
            details=details,
        )
        session.add(notification_instance)
