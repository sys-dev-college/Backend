import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel

from app.modules.notifications.models import NotificationStatus, NotificationType
from app.modules.users.schemas import UserShort


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    status: NotificationStatus
    user: UserShort
    message: str
    created_at: datetime
    details: Optional[dict] = None


class NotificationList(RootModel):
    root: List[NotificationOut]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class NotificationUpdate(BaseModel):
    notification_id: uuid.UUID
    status: NotificationStatus
