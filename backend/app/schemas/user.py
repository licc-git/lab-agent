from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator
from typing import Optional, List, Literal


class PasswordUpdateRequest(BaseModel):

    old_password: str = Field(..., min_length=6, max_length=12)
    new_password: str = Field(..., min_length=6, max_length=12)


class UserUpdateRequest(BaseModel):

    name: Optional[str] = Field(None, min_length=1, max_length=6)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    email: Optional[EmailStr] = Field(None, max_length=128)
    avatar: Optional[str] = Field(None, max_length=255)
    role: Literal["admin", "student"] = Field(default="student")
    status: Literal[0, 1] = Field(default=1)

    @model_validator(mode="after")
    def check_at_least_one(self):
        if all(v is None for v in (self.name, self.phone, self.email, self.avatar)):
            raise ValueError("至少提供一项要修改的字段")
        return self


class UserCreateRequest(BaseModel):

    username: Optional[str] = Field(..., min_length=3, max_length=12)
    password: str = Field(min_length=6, max_length=12, default="123456")
    name: Optional[str] = Field(None, min_length=1, max_length=6)
    avatar: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    email: Optional[EmailStr] = Field(None, max_length=128)
    role: Literal["admin", "student"] = Field(default="student")
    status: Literal[0, 1] = Field(default=1)


class UserDeleteListRequest(BaseModel):

    ids: List[int] = Field(..., min_length=1)


class UserResponse(BaseModel):

    id: int
    username: str
    name: Optional[str] = None
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):

    data: List[UserResponse]
    total: int
