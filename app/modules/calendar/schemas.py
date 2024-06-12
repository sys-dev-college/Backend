import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel

from app.modules.calendar.models import CalendarType
from app.modules.tasks.schemas import TaskOut
from app.modules.users.schemas import UserShort


class CalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheduled: datetime
    title: str
    type: CalendarType
    tasks: Optional[List[TaskOut]] = []
    assigner: Optional[UserShort] = None
    user: Optional[UserShort] = None


class CalendarList(RootModel):
    root: List[CalendarOut]


class CalendarFilter(BaseModel):
    user_id: Optional[uuid.UUID] = None
    scheduled: date


class CalendarIn(BaseModel):
    user_id: uuid.UUID
    scheduled: datetime
    title: str
    type: CalendarType
