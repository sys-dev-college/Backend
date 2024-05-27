import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import FetchedValue, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=FetchedValue(),
    )
    title: Mapped[str] = mapped_column(nullable=False)
    archived: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default=FetchedValue(),
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    users: Mapped[Optional[List["User"]]] = relationship(
        "User",
        secondary="user_chat",
        back_populates="chats",
        lazy="noload",
        cascade="all",
    )
    messages: Mapped[Optional[List["Message"]]] = relationship(
        "Message",
        back_populates="chat",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=FetchedValue(),
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="messages",
    )


class UserChat(Base):
    __tablename__ = "user_chat"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chat_id",
            name="uq_user_chat",
        ),
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=True,
    )
    chat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=True,
    )
