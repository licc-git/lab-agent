import json

from datetime import datetime as dt
from typing import Annotated, Literal, TypedDict
from langgraph.prebuilt import ToolNode
from sqlalchemy.orm import Session
from langchain.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph, add_messages

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import agent_tools
from app.models.prompts import ConversationLog

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


tools = agent_tools.build_tools()
model = init_chat_model(
    model_provider=settings.MODEL_PROVIDER,
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0,
)
model_with_tools = model.bind_tools(tools)  # 绑定工具
MAX_LLM_CALLS = 6
SYSTEM_MESSAGE = SystemMessage(content=SYSTEM_PROMPT)


class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    llm_calls: int


def _add_conversation(db, user_id, content, role):
    clog = ConversationLog(
        user_id=user_id,
        title="%s" % dt.strftime(dt.today(), "%Y%m%d"),
        content=json.dumps({"role": role, "content": content}, ensure_ascii=False),
    )
    db.add(clog)
    db.commit()


def llm_call(state: MessageState):
    return {
        "messages": [model_with_tools.invoke([SYSTEM_MESSAGE] + state["messages"])],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def should_continue(state: MessageState) -> Literal["tool_node", "__end__"]:
    messages = state["messages"]
    lastest_message = messages[-1]
    if state.get("llm_calls", 0) >= MAX_LLM_CALLS:
        return "__end__"
    if getattr(lastest_message, "tool_calls", []):
        return "tool_node"
    else:
        return "__end__"


def build_agent():
    agent_builder = StateGraph(MessageState, context_schema=agent_tools.UserContext)

    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", ToolNode(list(tools)))

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_call")

    return agent_builder.compile()


def run_agent(data: ChatRequest, db: Session, current_user: User):

    history_messages = []
    if not data.messages:
        raise BusinessException("消息不能为空")

    latest_user_query = next(msg.content for msg in reversed(data.messages) if msg.role == "user")
    _add_conversation(db, current_user.id, latest_user_query, "user")

    for message in data.messages:
        if message.role == "user":
            history_messages.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            history_messages.append(AIMessage(content=message.content))

    invoke_kwargs: MessageState = {"messages": history_messages, "llm_calls": 0}
    agent = build_agent()
    result = agent.invoke(
        invoke_kwargs, context=agent_tools.UserContext(db, current_user)
    )
    content = result["messages"][-1].content
    _add_conversation(db, current_user.id, content, "assistant")

    return ChatMessage(role="assistant", content=content)

"""
# Agent 的工作流
```
用户输入
   ↓
调用语言模型
   ↓
模型是否请求调用工具？
   ├── 否 → 生成最终回答
   │
   └── 是
        ↓
      执行工具
        ↓
      获得工具结果
        ↓
      再次调用模型
        ↓
      继续判断是否需要工具
```
"""
