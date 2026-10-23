from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.config import UPLOAD_DIR
from app.database import Base, engine
from app.api import api
from app import models
from app.services.reservation_service import expire_pending_reservations
from app.utils.logger import logger
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.common.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.utils.request_id import RequestIdMiddleware

Base.metadata.create_all(bind=engine)

origins = ["http://127.0.0.1:5173", "http://localhost:5173"]

reservation_scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.reservation_scheduler = (
        reservation_scheduler  # 把调度器实例挂到 app.state 上
    )
    reservation_scheduler.add_job(
        expire_pending_reservations,
        trigger="interval",
        minutes=10,
        id="expire_pending_reservations",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    reservation_scheduler.start()
    # logger.info("Reservation expiration scheduler started (interval=10 minutes)")
    try:
        yield
    finally:
        reservation_scheduler.shutdown(wait=True)
        logger.info("Reservation expiration scheduler stopped")


app = FastAPI(lifespan=lifespan)

# 跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIdMiddleware)

# 注册路由
app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(
    StarletteHTTPException, http_exception_handler
)  # 兜住 Starlette 的
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
# 挂载静态资源：/uploads/xxx.jpg → uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "Hello FastAPI"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8088)
