import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    unit: str
    completed: bool


class TaskList(RootModel):
    root: List[TaskOut]


class TaskIn(BaseModel):
    calendar_id: uuid.UUID
    name: str
    amount: int
    unit: str
    completed: Optional[bool] = False


class UpdateTask(BaseModel):
    name: Optional[str]
    amount: Optional[int]
    unit: Optional[str]


class TaskFilter(BaseModel):
    calendar_id: uuid.UUID
