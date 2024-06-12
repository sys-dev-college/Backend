import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    FetchedValue,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.session import Base
from app.utils.crud_model_mixin import ModelCRUDMixin

if TYPE_CHECKING:
    from app.modules.calendar.models import Calendar


class Task(Base, ModelCRUDMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=FetchedValue(),
    )
    calendar_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "calendars.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        nullable=True
    )
    unit: Mapped[str] = mapped_column(
        nullable=True,
    )
    completed: Mapped[bool] = mapped_column(
        default=False,
        server_default=FetchedValue(),
        nullable=False
    )
    calendar: Mapped["Calendar"] = relationship(
        "Calendar",
        back_populates="tasks"
    )


