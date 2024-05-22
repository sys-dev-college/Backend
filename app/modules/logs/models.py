import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, FetchedValue, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    # from app.modules.documents.models import Document
    # from app.modules.rooms.models import Room
    from app.modules.user_sessions.models import Session
    from app.modules.users.models import User


class Logs(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    document_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    room_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("rooms.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_session.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="logs",
    )
    session: Mapped[Optional["Session"]] = relationship(
        "Session",
        back_populates="logs",
    )


class LogAction(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    action_name_rus: Mapped[str] = mapped_column(Text(collation="default"), nullable=False)
    action_name_eng: Mapped[str] = mapped_column(Text(collation="default"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(collation="default"), nullable=True)
