from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from backend.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    username: str
    role: UserRole = UserRole.USER
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str]
    username: str
    role: UserRole
    department: Optional[str]
    is_approved: bool
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserUpdate(BaseModel):
    is_approved: Optional[bool] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None