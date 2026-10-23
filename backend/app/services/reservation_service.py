from datetime import datetime

from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from typing import Optional

from app.common.enums import ReservationStatus
from app.common.exceptions import BusinessException
from app.models import Reservation, User
from app.schemas.reservation import (
    ReservationCreateRequest,
    ReservationListResponse,
    ReservationResponse,
)
from app.models import Lab, Equipment, Reservation
from app.utils.logger import logger
from app.utils.common import escape_like
from app.database import SessionLocal, engine


def get_reservation_list(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: Optional[ReservationStatus] = None,
    keywords: Optional[str] = None,
    user_name: Optional[str] = None,
):
    query = db.query(Reservation)
    if current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)
    if keywords:
        query = query.filter(
            or_(
                Reservation.equipment.has(
                    Equipment.name.ilike(f"%{escape_like(keywords)}%")
                ),
                Reservation.lab.has(Lab.name.ilike(f"%{escape_like(keywords)}%")),
            )
        )
    if user_name:
        query = query.filter(
            Reservation.user.has(
                or_(
                    User.name.ilike(f"%{escape_like(user_name)}%"),
                    User.username.ilike(f"%{escape_like(user_name)}%"),
                )
            )
        )
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = []
    for item in items:
        data.append(
            ReservationResponse.model_validate(
                {
                    "id": item.id,
                    "user_name": (
                        item.user.name if item.user.name else item.user.username
                    ),
                    "reserve_type": "设备" if item.equipment_id else "实验室",
                    "lab_name": item.lab.name,
                    "equipment_name": (
                        item.equipment.name if item.equipment_id else None
                    ),
                    "reserve_date": item.reserve_date,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "remark": item.remark,
                    "status": item.status,
                }
            )
        )

    return ReservationListResponse(data=data, total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    pending_approval = (
        db.query(Reservation)
        .filter(
            Reservation.id == reservation_id,
            Reservation.status == ReservationStatus.PendingApproval,
        )
        .first()
    )
    if pending_approval is None:
        raise BusinessException("不存在此条预约信息待审核")
    if pending_approval.user_id != current_user.id:
        raise BusinessException(message="无权限", code=403)
    pending_approval.status = ReservationStatus.Cancelled
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: ReservationStatus):
    if status not in (ReservationStatus.Approved, ReservationStatus.Rejected):
        raise BusinessException("审核状态错误")
    pending_approval = (
        db.query(Reservation)
        .filter(
            Reservation.id == reservation_id,
            Reservation.status == ReservationStatus.PendingApproval,
        )
        .first()
    )
    if pending_approval is None:
        raise BusinessException("不存在此条预约信息待审核")
    pending_approval.status = status
    db.commit()


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException("实验室不存在")
    if lab.status != 1:
        raise BusinessException("实验室未开放")

    lab_open_days = lab.open_days
    lab_open_time, lab_close_time = lab.open_time, lab.close_time
    if data.reserve_date.weekday() not in lab_open_days:
        raise BusinessException("预约时间必须在实验室开放时段内")
    if data.start_time < lab_open_time or data.end_time > lab_close_time:
        raise BusinessException("预约时间必须在实验室开放时段内")

    if data.equipment_id:
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == data.equipment_id, Equipment.lab_id == data.lab_id)
            .first()
        )
        if not equipment:
            raise BusinessException("实验室不存在此设备")
        if equipment.status == 0:
            raise BusinessException("实验室此设备正在维修")

    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.reserve_date == data.reserve_date,
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
        Reservation.status.in_(
            [ReservationStatus.Approved, ReservationStatus.PendingApproval]
        ),
    )

    if data.equipment_id:
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:
        query = query.filter(Reservation.equipment_id.is_(None))

    is_busy = query.first()
    if is_busy:
        raise BusinessException("该时段已被预约")

    reservation_model = Reservation(**data.model_dump(), user_id=current_user.id)
    db.add(reservation_model)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicate = (
            db.query(Reservation.id)
            .filter(
                Reservation.lab_id == data.lab_id,
                Reservation.equipment_id == data.equipment_id,
                Reservation.reserve_date == data.reserve_date,
                Reservation.start_time == data.start_time,
            )
            .first()
        )
        if duplicate:
            logger.warning(
                "Duplicate reservation rejected lab_id=%s equipment_id=%s "
                "reserve_date=%s start_time=%s",
                data.lab_id,
                data.equipment_id,
                data.reserve_date,
                data.start_time,
            )
            raise BusinessException("该时段已被预约") from None
        logger.error(
            "Reservation insert failed with database integrity error "
            "lab_id=%s equipment_id=%s reserve_date=%s start_time=%s error_type=%s",
            data.lab_id,
            data.equipment_id,
            data.reserve_date,
            data.start_time,
            type(exc).__name__,
        )
        raise


def expire_pending_reservations() -> int:
    lock_name = "lab_agent_expire_pending_reservations"
    lock_connection = engine.connect()
    db: Session | None = None
    lock_acquired = False
    try:
        lock_result = (
            lock_connection.execute(
                text("SELECT GET_LOCK(:lock_name, 0)"),
                {"lock_name": lock_name},
            ).scalar()
        )
        if lock_result is None:
            raise RuntimeError(f"MySQL failed to acquire advisory lock {lock_name}")
        if lock_result == 0:
            logger.info("Skipped expiring reservations because another worker holds the lock")
            return 0
        if lock_result != 1:
            raise RuntimeError(
                f"MySQL returned unexpected result while acquiring lock {lock_name}: "
                f"{lock_result}"
            )
        lock_acquired = True
        db = SessionLocal()

        now = datetime.now()
        expired_count = (
            db.query(Reservation)
            .filter(
                Reservation.status == ReservationStatus.PendingApproval,
                or_(
                    Reservation.reserve_date < now.date(),
                    and_(
                        Reservation.reserve_date == now.date(),
                        Reservation.end_time <= now.time(),
                    ),
                ),
            )
            .update(
                {Reservation.status: ReservationStatus.Expired},
                synchronize_session=False,
            )
        )
        if expired_count:
            db.commit()
        # logger.info("Expired %s pending reservations", expired_count)
        return expired_count
    except Exception:
        if db is not None:
            db.rollback()
        logger.exception("Failed to expire pending reservations")
        raise
    finally:
        try:
            if lock_acquired:
                release_result = (
                    lock_connection.execute(
                        text("SELECT RELEASE_LOCK(:lock_name)"),
                        {"lock_name": lock_name},
                    ).scalar()
                )
                if release_result != 1:
                    raise RuntimeError(
                        f"Failed to release MySQL advisory lock {lock_name}"
                    )
        except Exception:
            logger.exception("Failed to release reservation expiration lock")
            raise
        finally:
            try:
                if db is not None:
                    db.close()
            finally:
                lock_connection.close()
