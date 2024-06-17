import uuid
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, RootModel


class AuthCredentials(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    email: str
    password: str
    is_accepted_agreement: bool = False
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    is_admin: Optional[bool] = "user"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class UserShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_name: str = Field(serialization_alias="name")
    email: str


class Token(BaseModel):
    access_token: str
    refresh_token: str


class UserExists(BaseModel):
    email: EmailStr


class UserExistsOut(BaseModel):
    user_exists: bool


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    description: Optional[str]


class UserGroupShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class UserGroupList(RootModel):
    model_config = ConfigDict(
        json_encoders={List[UserGroupShort]: lambda fields: [str(field.id) for field in fields]}
    )

    root: List[UserGroupShort]


class UsersWithGroups(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    groups: UserGroupList = Field(serialization_alias="group")
    role: Optional[str] = None


class UserWithGroupsList(RootModel):
    root: List[UsersWithGroups]


class ListOfUsersWithGroups(BaseModel):
    users: List[UsersWithGroups]


class UserRoomStatusChoice(int, Enum):
    PUBLIC = 0
    WAITING_FOR_APPROVE = 1
    APPROVED = 2
    DENIED = 3


class UpdateUserRoomStatus(BaseModel):
    room_id: uuid.UUID
    status: UserRoomStatusChoice


class UserLogout(BaseModel):
    access_token: str
    refresh_token: str


class EmailRestorePassword(BaseModel):
    email: EmailStr


class RestorePassword(BaseModel):
    user_id: uuid.UUID
    password: str


class UserParamIn(BaseModel):
    name: str
    amount: str


class UserParamOut(UserParamIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user: UserShort
