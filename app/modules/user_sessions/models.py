import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    ColumnElement,
    FetchedValue,
    ForeignKey,
    and_,
    desc,
    func,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import AsyncSession, Base

if TYPE_CHECKING:
    from app.modules.logs.models import Logs


class Session(Base):
    __tablename__ = "user_session"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    fingerprint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_fingerprint.id"),
        nullable=False,
    )
    ip: Mapped[str] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column()
    start_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
    end_at: Mapped[Optional[datetime]] = mapped_column()

    state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    logs: Mapped[List["Logs"]] = relationship(
        "Logs",
        # secondary="logs_to_session",
        back_populates="session",
        lazy="noload",
    )

    @staticmethod
    async def get_ws_session_by_conditions(
        session: AsyncSession,
        *conditions: ColumnElement[bool],
    ) -> Optional["Session"]:
        query = select(Session).where(and_(*conditions)).order_by(desc(Session.start_at))
        res = await session.scalar(query)
        return res
