# from typing import AsyncGenerator

from sqlalchemy.orm import sessionmaker, DeclarativeBase
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession  # 改用异步引擎和会话
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import create_engine, DateTime, func
from datetime import datetime

from app.config import settings

engine = create_engine(
    url=settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=15,
    echo=False,
)


SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键ID", sort_order=-1
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, comment="创建时间", default=func.now(), sort_order=1
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
        sort_order=2,
    )


# #  换异步引擎
# engine = create_async_engine(
#     url=settings.DATABASE_URL,  # URL 也要换前缀！
#     pool_pre_ping=True,
#     pool_recycle=3600,
#     pool_size=5,
#     max_overflow=15,
#     echo=False,
# )

# # 换异步会话工厂，expire_on_commit=False 强烈建议
# AsyncSessionLocal = async_sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autoflush=False,
# )


# #  异步版 get_db
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionLocal() as db:  # ← async with，退出时自动 close
#         try:
#             yield db
#         except Exception:
#             await db.rollback()  # ← rollback 也是 await
#             raise
