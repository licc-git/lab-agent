from enum import IntEnum

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional, Literal

from app.common.response import Response
from app.common.exceptions import BusinessException
from app.database import get_db
from app.dependencies.auth import get_current_admin_user, get_current_user
from app.models.user import User
from app.schemas.lab import LabCreateRequest, LabUpdateRequest, LabDeleteListRequest
from app.services import lab_service

router = APIRouter(prefix="/lab", tags=["实验室管理"])


DBSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_admin_user)]


class LabStatus(IntEnum):
    CLOSED = 0
    OPEN = 1


@router.get("/list", response_model=Response)
def get_lab_list(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    page: Annotated[int, Query(ge=1, description="页码，从 1 开始")] = 1,
    page_size: Annotated[
        int, Query(ge=10, le=999, description="每页条数，12-512")
    ] = 10,
    status: Optional[LabStatus] = None,
    keywords: Annotated[
        Optional[str],
        Query(max_length=50, description="按名称/位置模糊搜索"),
    ] = None,
):
    res = lab_service.get_lab_page_list(db, page, page_size, status, keywords)
    return Response.success(data=res)


@router.get("/options", summary="实验室下拉选项（不分页，仅 id+name）")
def get_lab_options(
    current_user: CurrentUser,
    db: DBSession,
):
    return Response.success(data=lab_service.get_lab_options(db))


@router.post("", response_model=Response)
def create_lab(
    data: LabCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    res = lab_service.create_lab(db, data)
    return Response.success(data=res)


@router.put("/{lab_id}", response_model=Response)
def update_lab(
    lab_id: int,
    data: LabUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    res = lab_service.update_lab(db, lab_id, data)
    return Response.success(data=res)


# 注意：/batch 必须注册在 /{lab_id} 之前，否则 "batch" 会被当成 lab_id 做 int 校验
@router.delete("/batch", response_model=Response)
def delete_labs(
    data: LabDeleteListRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    count = lab_service.delete_labs(db, data.ids)
    if count == 0:
        raise BusinessException(message="没有匹配到可删除的实验室")
    return Response.success(message=f"成功删除 {count} 个实验室")


@router.get("/{lab_id}", response_model=Response)
def get_lab_detail(lab_id: Annotated[int, Path(ge=1, le=99)], db: DBSession):
    return Response.success(data=lab_service.get_lab_detail(db, lab_id))


@router.delete("/{lab_id}", response_model=Response)
def delete_lab(
    lab_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    lab_service.delete_lab(db, lab_id)
    return Response.success(message="删除成功")
