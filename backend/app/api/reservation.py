from fastapi import APIRouter, Depends, Path, Query
from typing import Annotated, Optional
from sqlalchemy.orm import Session

from app.common.enums import ReservationStatus
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin_user, get_current_user
from app.services import reservation_service
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest, ReservationStatusAudit

router = APIRouter(prefix="/reservation", tags=["实验室和设备预约"])


DBSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
PageParam = Annotated[int, Query(ge=1, description="页码，从 1 开始")]
PageSizeParam = Annotated[int, Query(ge=1, le=100, description="每页条数，最大 100")]
KeywordsParam = Annotated[
    Optional[str], Query(max_length=64, description="按实验室/设备模糊搜索")
]
UserNameParam = Annotated[Optional[str], Query(max_length=16, description="按姓名模糊搜索")]


@router.get("/list", response_model=Response, summary="获取预约列表")
def get_reservation_list(
    db: DBSession,
    current_user: CurrentUser,
    page: PageParam = 1,
    page_size: PageSizeParam = 10,
    status: Optional[ReservationStatus] = None,
    keywords: KeywordsParam = None,
    user_name: UserNameParam = None,
):
    return Response.success(
        data=reservation_service.get_reservation_list(
            db, current_user, page, page_size, status, keywords, user_name
        )
    )


@router.put("/{reservation_id}/cancel", response_model=Response, summary="学生取消预约")
def cancel_reservation(
    db: DBSession,
    current_user: CurrentUser,
    reservation_id: Annotated[int, Path(ge=1)]
):
    reservation_service.cancel_reservation(db, current_user, reservation_id)
    return Response.success()


@router.put("/{reservation_id}/audit", response_model=Response, summary="管理员操作预约")
def audit_reservation(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    reservation_id: Annotated[int, Path(ge=1)],
    status: ReservationStatusAudit,
):
    reservation_service.audit_reservation(db, reservation_id, status.status)
    return Response.success()


@router.post("", response_model=Response, summary="创建预约")
def create_reservation(
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    data: ReservationCreateRequest,
):
    reservation_service.create_reservation(db, current_user, data)
    return Response.success(message="预约成功")
