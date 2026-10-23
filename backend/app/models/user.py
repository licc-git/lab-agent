from typing import TYPE_CHECKING

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, SmallInteger, CheckConstraint


if TYPE_CHECKING:
    from app.models.reservation import Reservation

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户信息表"}

    username: Mapped[str] = mapped_column(
        String(16), index=True, unique=True, nullable=False, comment="账号"
    )
    password: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="密码(哈希)"
    )

    name: Mapped[str | None] = mapped_column(String(16), comment="昵称")
    email: Mapped[str | None] = mapped_column(String(128), comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), comment="手机号")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像URL")
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role"),
        default="student",
        server_default="student",  # 数据库层面也有默认值
        nullable=False,
        comment="角色",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        CheckConstraint("status IN (0, 1)", name="ck_user_status"),
        server_default="1",
        nullable=False,
        comment="状态：0-禁用，1-正常",
    )

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user",lazy="selectin")