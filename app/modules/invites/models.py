import uuid
from datetime import datetime

from sqlalchemy import FetchedValue, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=FetchedValue(),
    )
