import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel

from app.modules.calendar.models import CalendarType
from app.modules.tasks.schemas import TaskOut
from app.modules.users.schemas import UserShort


class CalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheduled: datetime
    type: CalendarType
    tasks: Optional[List[TaskOut]] = []
    assigner: UserShort
    user: UserShort


class CalendarList(RootModel):
    root: List[CalendarOut]
