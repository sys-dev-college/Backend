import datetime
import enum
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Enum,
    FetchedValue,
    ForeignKey,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.session import Base
from app.utils.crud_model_mixin import ModelCRUDMixin

if TYPE_CHECKING:
    from app.modules.tasks.models import Task
    from app.modules.users.models import User


class CalendarType(enum.IntEnum):
    FOOD = 0
    EXERCISE = 1


class Calendar(Base, ModelCRUDMixin):
    __tablename__ = "calendars"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=FetchedValue(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False
    )
    scheduled: Mapped[datetime.datetime] = mapped_column(
        nullable=True,
        default=func.now(),
        server_default=FetchedValue(),
    )
    assigner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=True
    )
    type: Mapped[CalendarType] = mapped_column(
        Enum(CalendarType),
        nullable=False
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="calendar",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="calendars",
    )
    assigner: Mapped["User"] = relationship(
        "User",
        back_populates="assigned_calendars"
    )


