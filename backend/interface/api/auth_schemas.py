from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


UserRole = Literal["individual", "enterprise", "admin"]


class UserSchema(BaseModel):
    id: int
    username: str
    display_name: str
    company_intro: Optional[str] = None
    role: UserRole
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserSchema


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=64)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class CreateProtocolRequest(BaseModel):
    target_user_id: int
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=10, max_length=10000)


class AdminEnterpriseUserSchema(BaseModel):
    id: int
    username: str
    company_name: str
    company_intro: str
    created_at: datetime


class AdminCreateEnterpriseUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    company_name: str = Field(min_length=1, max_length=64)
    company_intro: str = Field(default="", max_length=4000)


class AdminUpdateEnterpriseUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    company_name: str = Field(min_length=1, max_length=64)
    company_intro: str = Field(default="", max_length=4000)


class RoleProtocolSchema(BaseModel):
    id: int
    company_name: str
    title: str
    content: str
    status: str
    created_at: datetime
    signed_at: Optional[datetime]
    enterprise_user_id: Optional[int]
    target_user_id: Optional[int]
    target_user_display_name: Optional[str] = None
    target_username: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
