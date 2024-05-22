import uuid
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel

from app.modules.users.schemas import UserShort


class GetLogsByDocumentIdResponse(BaseModel):
    type: str
    name: str
    timestamp: str
    user_name: str


class DocumentObjOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    token: Optional[uuid.UUID]


class DocumentNameOut(BaseModel):
    name: str


class GetLogsByDocumentIdResponseSchema(RootModel):
    root: List[GetLogsByDocumentIdResponse]


class DocumentUnionSchema(RootModel):
    model_config = ConfigDict(
        from_attributes=True, json_encoders={str: lambda v: DocumentNameOut(name=v)}
    )

    root: Union[DocumentObjOut, str]


class GetLogResponseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.strftime("%d.%m.%Y, %H:%M:%S"),
        },
    )

    type: str
    name: str
    created_at: Optional[datetime] = Field(serialization_alias="timestamp")
    user: Optional[UserShort]
    document_id: Optional[uuid.UUID]
    document_name: Optional[DocumentUnionSchema] = Field(serialization_alias="entity")
    details: Optional[dict] = {}


class GetLogsList(RootModel):
    root: List[GetLogResponseSchema]

    def __iter__(self):  # type: ignore
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class FilterLog(BaseModel):
    user_id: Optional[uuid.UUID] = None
    room_id: Optional[uuid.UUID]


class ReportFilterLog(BaseModel):
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    action: Optional[str] = None
    document: Optional[uuid.UUID] = None


class ReportLog(BaseModel):
    room_id: uuid.UUID
    filters: Optional[ReportFilterLog] = None
