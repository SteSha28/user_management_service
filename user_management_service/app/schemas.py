from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Literal


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    # confirm_code: str
    password: str


class PasswordUpdate(BaseModel):
    confirm_code: str
    last_password: str
    password: str


class UserRecovery(BaseModel):
    email: EmailStr


class UserInfo(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    gender: Literal["male", "female", "not_specified"] = "not_specified"
    profile_image: str | None = None
    description: str | None = None


class UserUpdate(UserInfo):
    username: str | None = None
    email: EmailStr | None = None

    class Config:
        orm_mode = True


class User(UserBase, UserInfo):
    id: int

    class Config:
        orm_mode = True