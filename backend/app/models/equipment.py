from typing import Optional, Literal, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.lab import Lab
    from app.models.reservation import Reservation

class Equipment(Base):
    __tablename__ = "equipments"
    __table_args__ = (
        CheckConstraint("status IN (0, 1)", name="ck_equipments_status"),
        {"comment": "实验室设备表"},
    )

    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), comment="所属实验室")
    name: Mapped[str] = mapped_column(String(64), comment="设备名称")
    description: Mapped[Optional[str]] = mapped_column(String(512), comment="说明")
    img: Mapped[Optional[str]] = mapped_column(String(256), comment="图片")
    spec: Mapped[Optional[str]] = mapped_column(String(128), comment="型号规格") 
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), comment="数量")
    status: Mapped[Literal[0, 1]] = mapped_column(
        Integer, default=1, server_default=text("1"), comment="状态：0-维修，1-正常"
    )

    lab: Mapped["Lab"] = relationship(back_populates="equipments")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="equipment", lazy="selectin")
