from datetime import time
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Time, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.reservation import Reservation


class Lab(Base):
    __tablename__ = "labs"
    __table_args__ = {"comment": "实验室信息表"}

    name: Mapped[str] = mapped_column(String(20), unique=True, comment="实验室名称")
    location: Mapped[str | None] = mapped_column(String(50), comment="位置")
    capacity: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="容纳人数"
    )

    open_time: Mapped[time] = mapped_column(
        Time, default=time(8), server_default="8:00:00", comment="每日开放开始时间"
    )
    close_time: Mapped[time] = mapped_column(
        Time, default=time(19), server_default="19:00:00", comment="每日开放结束时间"
    )
    open_days: Mapped[list[int]] = mapped_column(
        JSON, default=lambda: [0, 1, 2, 3, 4], comment="每周开放日，0为周一"
    )

    description: Mapped[str | None] = mapped_column(String(512), comment="简介")
    img: Mapped[str | None] = mapped_column(String(256), comment="封面图")

    status: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", comment="状态：0-关闭，1-开放"
    )

    equipments: Mapped[list["Equipment"]] = relationship(back_populates="lab")
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="lab", lazy="selectin"
    )
