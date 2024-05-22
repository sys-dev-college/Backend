import uuid
from enum import Enum
from typing import List

from pydantic import BaseModel


class InviteLinkType(str, Enum):
    master = "master"
    common = "common"


class InviteLinkData(BaseModel):
    type: InviteLinkType
    emails: List[str]
    room_id: uuid.UUID
    group_id: uuid.UUID
