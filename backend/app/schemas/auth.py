from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse
from typing import Optional
from pydantic import Field, EmailStr


class LoginRequest(BaseModel):

    username: str = Field(..., min_length=3, max_length=12)
    password: str = Field(..., min_length=6, max_length=12)


class RegisterRequest(BaseModel):

    username: str = Field(..., min_length=3, max_length=12)
    password: str = Field(..., min_length=6, max_length=12)


class LoginResponse(BaseModel):

    token: str
    user: UserResponse
