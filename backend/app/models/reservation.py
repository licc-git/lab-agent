from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer,
    String,
    TIME,
    ForeignKey,
    DATE,
    CheckConstraint,
    UniqueConstraint,
    text,
)
from typing import Optional, TYPE_CHECKING
from datetime import time, date
from app.database import Base

if TYPE_CHECKING:
    from app.models.lab import Lab
    from app.models.equipment import Equipment
    from app.models.user import User


class Reservation(Base):

    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint(
            sqltext="status in (0, 1, 2, 3, 4)", name="check_reservation_status"
        ),
        UniqueConstraint(
            "lab_id",
            "equipment_id",
            "reserve_date",
            "start_time",
            name="uq_lab_equip_time",
        ),
        {"comment": "实验室以及设备预约表"},
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), comment="用户ID"
    )
    lab_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("labs.id"), comment="实验室ID"
    )
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), comment="设备ID"
    )
    reserve_date: Mapped[date] = mapped_column(DATE, comment="预约日期")
    start_time: Mapped[time] = mapped_column(TIME, comment="预约开始时间")
    end_time: Mapped[time] = mapped_column(TIME, comment="预约结束时间")
    remark: Mapped[Optional[str]] = mapped_column(String(64), comment="备注")
    status: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        comment="预约状态：0-待审核，1-已通过，2-已拒绝，3-已取消，4-已过期",
    )

    lab: Mapped["Lab"] = relationship(back_populates="reservations", lazy="joined")
    equipment: Mapped["Equipment"] = relationship(
        back_populates="reservations", lazy="joined"
    )
    user: Mapped["User"] = relationship(back_populates="reservations", lazy="joined")
