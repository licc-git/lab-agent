from pydantic import BaseModel, Field
from typing import Any, Optional


class Response(BaseModel):
    code: int = Field(ge=100, lt=599)
    message: str
    data: Optional[Any] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "请求成功"):
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str = "请求失败"):
        return cls(code=code, message=message)
