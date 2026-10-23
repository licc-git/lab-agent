from fastapi import Depends, Query
from typing import Annotated
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, LoginResponse
from app.schemas.user import (
    UserCreateRequest,
    UserDeleteListRequest,
    UserResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
    UserListResponse,
)
from app.utils.password import verify_password, hash_password
from app.common.exceptions import BusinessException
from app.utils.jwt import create_access_token


def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password):
        raise BusinessException("账号或密码错误")
    if user.status != 1:
        raise BusinessException("账号已被禁用")
    token = create_access_token(user.id)

    return LoginResponse(token=token, user=UserResponse.model_validate(user))


def register(data: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    cnt = db.query(User).filter(User.username == data.username).count()
    if cnt > 0:
        raise BusinessException("用户已存在，请重新输入用户名")

    user = User(
        username=data.username,
        password=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)


def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def update_user_info(data: UserUpdateRequest, user: User, db: Session) -> UserResponse:
    user_dict = data.model_dump(exclude_none=True, exclude={"role", "status", "password"})
    for k, v in user_dict.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_password(data: PasswordUpdateRequest, user: User, db: Session):
    if not verify_password(data.old_password, user.password):
        raise BusinessException("原密码错误")
    if data.old_password == data.new_password:
        raise BusinessException(message="新密码不能与原密码相同")
    user.password = hash_password(data.new_password)
    db.commit()


def get_user_page_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    username: str | None = None,
    name: str | None = None,
):
    query = db.query(User)

    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    total = query.count()
    user_list = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return UserListResponse(
        data=[UserResponse.model_validate(item) for item in user_list],
        total=total,
    )


def create_user(db: Session, data: UserCreateRequest):
    cnt = db.query(User).filter(User.username == data.username).count()
    if cnt > 0:
        raise BusinessException("用户已存在，请重新输入")
    user = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name,
        role=data.role,
        email=data.email,
        phone=data.phone,
        avatar=data.avatar,
        status=data.status,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def update_user(db: Session, user_id: int, current_user: User, data: UserUpdateRequest):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException("用户不存在")
    if user.role == "admin" and current_user.id != user_id:
        raise BusinessException("不能修改其他超级管理员账号")
    for fied, value in data.model_dump(exclude_none=True).items():
        setattr(user, fied, value)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: int, current_user: User):
    if current_user.id == user_id:
        raise BusinessException("不能删除当前登录的账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException("用户不存在")
    if user.role == "admin":
        raise BusinessException("不能删除管理员的账号")
    db.delete(user)
    db.commit()

def delete_user_list(db: Session, data: UserDeleteListRequest, current_user: User):
    # 去重并排除当前登录账号（不允许删除自己）
    ids = {i for i in data.ids if i != current_user.id}
    if not ids:
        raise BusinessException("不能删除当前登录的账号")
    deleted = (
        db.query(User)
        .filter(User.id.in_(ids), User.role != "admin")
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted}
