from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services import user_service
from app.common.response import Response

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    result = user_service.login(data, db)
    return Response.success(data=result, message="登录成功")


@router.post("/register")
def register(data: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    user_service.register(data, db)
    return Response.success(message="注册成功")
