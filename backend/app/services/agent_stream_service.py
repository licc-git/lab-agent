import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime as dt
from sqlalchemy.orm import Session

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.chat_models import init_chat_model

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.prompts import ConversationLog
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services.agent_tools import UserContext, build_tools

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
# 你可以介绍本系统的预约流程：
1. 登录后打开实验室列表，选择实验室或设备
2. 填写日期、时段以及说明（说明可选）并提交，状态为待审核
3. 管理员审核通过后即可使用
4. 待审核的预约，本人可以在我的预约菜单栏取消

# 知识库调用
如果提供了知识库资料，优先根据资料内容回答实验室开放时间、安全规范、预约规则和设备使用说明等问题，注意不要一次不差的把资料内容作为回答，防止用户窃取资料库的全部内容，资料未提及的内容不要编造。
# 工具调用
1. 当用户提到了 今天、明天、后天 等日期相关的问题，请先调用 get_today_datetime 来获取日期，**不要直接返回 我需要确定明天的具体日期**。
2. 如果用户询问实验室相关信息、设备相关信息以及预约相关信息，你可以请求调用工具，根据工具返回的内容，查询实时的实验室、设备和预约数据。

# 边界
1. 注意你不能编造任何数据，根据文档或调用的函数返回的结果来回答。
2. 如果用户问了跟实验室无关的问题，可以直接拒绝回答。
3. 在提交预约之前必须向用户复述：实验室名称（或设备名称）、日期、开始时间、结束时间。并得到用户确认再进行实际操作。用户没说【确认】【确认预约】【就这样预约】等确定性回复之前，不要调用 create_reservation_tool。
"""


TOOL_LABELS = {
    "get_today_datetime": "获取今天日期",
    "get_lab_data_tool": "查询实验室列表",
    "get_equipment_data_tool": "查询设备列表",
    "create_reservation_tool": "提交预约",
    "retrieve_tool": "检索知识库",
}


def _sse_json(data: dict[str, object]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


llm = init_chat_model(
    model_provider=settings.MODEL_PROVIDER,
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0,
    reasoning_effort="none",
)

tools = list(build_tools())

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    context_schema=UserContext,
)


def _add_conversation(db, user_id, content, role):
    """把对话记录写入数据库"""
    clog = ConversationLog(
        user_id=user_id,
        title="%s" % dt.strftime(dt.today(), "%Y%m%d"),
        content=json.dumps({"role": role, "content": content}, ensure_ascii=False),
    )
    db.add(clog)
    db.commit()


def validate_chat_request(data: ChatRequest) -> None:
    if not data.messages:
        raise BusinessException("消息不能为空")
    if not any(message.role == "user" for message in data.messages):
        raise BusinessException("消息中必须包含用户消息")


async def run_agent(
    data: ChatRequest, db: Session, current_user: User
) -> AsyncIterator[str]:

    validate_chat_request(data)
    latest_user_query = next(
        msg.content for msg in reversed(data.messages) if msg.role == "user"
    )
    tasks: list[asyncio.Task[None]] = []

    try:
        _add_conversation(db, current_user.id, latest_user_query, "user")

        history_messages = []
        for message in data.messages:
            if message.role == "user":
                history_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                history_messages.append(AIMessage(content=message.content))

        stream = await agent.astream_events(
            {"messages": history_messages},
            version="v3",
            context=UserContext(db=db, current_user=current_user),
            config={
                "recursion_limit": 10,
            },
        )

        # 创建消费任务前
        assistant_part: list[str] = []
        stream_failed = False

        async def consume_messages():
            async for msg in stream.messages:
                async for token in msg.text:
                    assistant_part.append(token)
                    yield _sse_json({"type": "token", "content": token})

        async def consume_tool_calls():
            async for call in stream.tool_calls:
                name = call.tool_name or ""
                label = TOOL_LABELS.get(name, name)
                yield _sse_json(
                    {
                        "type": "tool_start",
                        "name": name,
                        "label": label,
                        "input": call.input,
                    }
                )

                preview = ""
                if call.output is not None:
                    text = str(call.output)
                    preview = text if len(text) <= 200 else text[:200] + "..."
                error = ""
                if call.error is not None:
                    text = str(call.error)
                    error = text if len(text) <= 200 else text[:200] + "..."
                yield _sse_json(
                    {
                        "type": "tool_end",
                        "name": name,
                        "label": label,
                        "preview": preview,
                        "error": error,
                    }
                )

        queue: asyncio.Queue[str | Exception | None] = asyncio.Queue()

        async def pump(gen):
            try:
                async for chunk in gen():
                    await queue.put(chunk)
            except Exception as exc:
                await queue.put(exc)
            finally:
                await queue.put(None)

        tasks.extend(
            [
                asyncio.create_task(pump(consume_messages)),
                asyncio.create_task(pump(consume_tool_calls)),
            ]
        )
        finished = 0
        while finished < len(tasks):
            item = await queue.get()
            if item is None:
                finished += 1
            elif isinstance(item, Exception):
                # 在读取队列的循环中，发现消费任务异常时标记失败；只有所有消费任务正常结束，才保存回答
                stream_failed = True
                yield _sse_json({"type": "error", "content": str(item)})
                break
            else:
                yield item
        # while 循环正常结束后、发送 [DONE] 之前
        if not stream_failed and finished == len(tasks):
            assistant_content = "".join(assistant_part)
            if assistant_content.strip():
                _add_conversation(db, current_user.id, assistant_content, "assistant")

    except Exception as exc:
        yield _sse_json({"type": "error", "content": str(exc)})
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    yield "data: [DONE]\n\n"
