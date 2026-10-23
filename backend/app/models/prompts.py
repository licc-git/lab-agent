from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    __table_args__ = {"comment": "用户对话日志"}

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="所属用户ID",
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, comment="对话消息")
