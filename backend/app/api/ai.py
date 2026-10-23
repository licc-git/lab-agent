from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Annotated
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.services import ai_service, agent_service, agent_stream_service
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest

router = APIRouter(prefix="/ai", tags=["AI相关"])


@router.get("/chat", summary="AI对话历史记录")
def get_chat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return Response.success(data=ai_service.get_chat(db, current_user))


@router.post("/chat", summary="AI对话")
def chat(data: ChatRequest, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return Response.success(data=agent_service.run_agent(data, db, current_user))
    # return Response.success(data=ai_service.chat(data, db, current_user))


@router.post("/chat/stream", summary="AI对话")
async def chat_stream(data: ChatRequest, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    agent_stream_service.validate_chat_request(data)
    return StreamingResponse(
        content=agent_stream_service.run_agent(data, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲，否则前端收不到实时流
        },
    )
