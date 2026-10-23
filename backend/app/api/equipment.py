from fastapi import APIRouter, Depends, Query
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from app.common.response import Response
from app.models import User
from app.dependencies.auth import get_current_admin_user, get_current_user
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
    EquipmentDeleteListRequest,
)
from app.services import equipment_service
from app.database import get_db
from app.common.exceptions import BusinessException

router = APIRouter(prefix="/equipment", tags=["实验室设备信息接口"])

CurrentUser = Annotated[User, Depends(get_current_admin_user)]
DBSession = Annotated[Session, Depends(get_db)]

PageParam = Annotated[int, Query(ge=1, description="页码，从 1 开始")]
PageSizeParam = Annotated[int, Query(ge=1, le=100, description="每页条数，最大 100")]
KeywordsParam = Annotated[Optional[str], Query(max_length=64, description="按名称/型号模糊搜索")]
LabIdParam = Annotated[Optional[int], Query(gt=0, description="按实验室 ID 过滤")]


@router.get("/list", summary="分页查询设备列表")
def get_equipment_list(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    page: PageParam = 1,
    page_size: PageSizeParam = 10,
    keywords: KeywordsParam = None,
    lab_id: LabIdParam = None,
):
    """分页模糊查询实验室设备，支持按实验室过滤"""
    res = equipment_service.get_equipment_page_list(
        db, page, page_size, keywords, lab_id
    )
    return Response.success(data=res)


@router.post("", summary="新增设备")
def create_equipment(
    data: EquipmentCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    res = equipment_service.create_equipment(db, data)
    return Response.success(data=res)


@router.put("/{equipment_id}", summary="更新设备")
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    res = equipment_service.update_equipment(db, equipment_id, data)
    return Response.success(data=res)


@router.delete("/batch")
def delete_equipments(
    data: EquipmentDeleteListRequest, 
    current_user: CurrentUser, 
    db: DBSession
):
    count = equipment_service.delete_equipments(db, data.ids)
    if count == 0:
        raise BusinessException(message="没有匹配到可删除的设备")
    return Response.success(message=f"成功删除 {count} 个设备")


@router.delete("/{equipment_id}", summary="删除设备")
def delete_equipment(
    equipment_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    equipment_service.delete_equipment(db, equipment_id)
    return Response.success(message="删除成功")
