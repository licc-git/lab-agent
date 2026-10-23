from typing import Annotated
from fastapi import Depends, APIRouter, Path, Query
from sqlalchemy.orm import Session
from websockets import route

from app.dependencies.auth import get_current_user, get_current_admin_user
from app.common.response import Response
from app.services import user_service
from app.models.user import User
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserDeleteListRequest,
    PasswordUpdateRequest,
)
from app.database import get_db

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/profile")
def get_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    return Response.success(user_service.get_user_info(current_user))


@router.put("/profile")
def update_user_info(
    data: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return Response.success(user_service.update_user_info(data, current_user, db))


@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    user_service.update_password(data, current_user, db)
    return Response.success(message="密码修改成功")


@router.get("/list")
def get_user_page_list(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=10, le=100)] = 10,
    username: Annotated[str | None, Query(max_length=16)] = None,
    name: Annotated[str | None, Query(max_length=16)] = None,
):
    return Response.success(
        data=user_service.get_user_page_list(db, page, page_size, username, name)
    )


@router.post("")
def create_user(
    db: Annotated[Session, Depends(get_db)],
    data: UserCreateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    return Response.success(data=user_service.create_user(db, data), message="创建成功")


# 注意：/batch 必须注册在 /{user_id} 之前，否则 "batch" 会被当成 user_id 做 int 校验
@router.delete("/batch")
def delete_user_list(
    data: UserDeleteListRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    return Response.success(
        data=user_service.delete_user_list(db, data, current_user),
        message="批量删除成功",
    )


@router.put("/{user_id}")
def update_user(
    user_id: Annotated[int, Path(ge=1, le=9999)],
    db: Annotated[Session, Depends(get_db)],
    data: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    return Response.success(
        data=user_service.update_user(db, user_id, current_user, data),
        message="更新成功",
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: Annotated[int, Path(ge=1, le=9999)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    return Response.success(
        data=user_service.delete_user(db, user_id, current_user), message="删除成功"
    )
