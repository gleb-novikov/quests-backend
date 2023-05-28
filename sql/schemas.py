from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str


class UserLogin(UserBase):
    password: str


class UserRegistration(UserLogin):
    name: str


class UserConfirm(BaseModel):
    activation_code: str


class UserResetCode(BaseModel):
    email: str
    activation_code: str


class UserResetNew(BaseModel):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserTempToken(UserBase):
    temp_token: str

    class Config:
        orm_mode = True


class User(UserBase):
    name: str
    token: str
    is_active: bool

    class Config:
        orm_mode = True


class Location(BaseModel):
    id: int
    latitude: float
    longitude: float
    story: str
    epilog: str

    class Config:
        orm_mode = True


class Quest(BaseModel):
    id: int
    name: str
    preview_url: str
    description: str
    time: int
    distance: int

    locations: list[Location] = []

    class Config:
        orm_mode = True


class Quests(BaseModel):
    quests: list[Quest] = []

    class Config:
        orm_mode = True


class Progress(BaseModel):
    quest_id: int
    location_id: int

    class Config:
        orm_mode = True


class ProgressObject(BaseModel):
    progress: list[Progress] = []

    class Config:
        orm_mode = True
