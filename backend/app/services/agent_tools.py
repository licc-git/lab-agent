from datetime import date, time, datetime
from dataclasses import dataclass, field
from langchain.tools import tool, ToolRuntime
from sqlalchemy.orm import Session
from threading import RLock
from typing import Any, Optional
from functools import wraps

from app.common.exceptions import BusinessException
from app.models import User
from app.schemas.reservation import ReservationCreateRequest
from app.utils.logger import logger

from .kb_service import retrieve
from .lab_service import get_lab_page_list
from .equipment_service import get_equipment_page_list
from .reservation_service import create_reservation


@dataclass
class UserContext:
    """定义上下文结构"""

    db: Session
    current_user: User
    db_lock: Any = field(default_factory=RLock, repr=False)


def handle_tool_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BusinessException as e:
            logger.error(str(e))
            return {"error": str(e)}
        except Exception as e:
            logger.error(str(e))
            raise
    return wrapper


def build_tools():

    @tool
    def retrieve_tool(query: str):
        """根据自然语言查询,从知识库中检索最相关的文档片段。

        当用户询问实验室、设备相关的使用、安全规范、开放时间以及预约等的非结构化信息时使用。
        返回 top 3 相关片段,字段 retrieve_data 为片段列表。

        参数:
            query: 用户的问题或检索关键词,使用自然语言即可。
        """

        items = retrieve(query, top_k=10, top_n=3)
        return {"retrieve_data": items}

    @tool
    @handle_tool_errors
    def get_lab_data_tool(
        runtime: ToolRuntime[UserContext],
        status: Optional[int] = None,
        keywords: Optional[str] = None,
    ):
        """分页查询实验室列表(第一页,每页 10 条)。

        当用户想浏览、查找实验室,或按状态/关键词筛选实验室时使用。

        参数:
            status: 实验室状态筛选（开放或关闭）
            keywords: 实验室名称或实验室地址的关键词
        """

        with runtime.context.db_lock:
            res = get_lab_page_list(
                runtime.context.db,
                page=1,
                page_size=10,
                status=status,
                keywords=keywords,
            ).model_dump(mode="json")
        return res

    @tool
    @handle_tool_errors
    def get_equipment_data_tool(
        runtime: ToolRuntime[UserContext],
        keywords: Optional[str] = None,
        lab_id: Optional[int] = None,
    ):
        """分页查询设备列表(第一页,每页 10 条)。

        当用户想浏览、查找设备,或查看某个实验室下的设备时使用。

        参数:
            keywords: 设备名称或型号的关键词。
            lab_id: 实验室 ID。
        """


        with runtime.context.db_lock:
            res = get_equipment_page_list(
                runtime.context.db,
                page=1,
                page_size=10,
                keywords=keywords,
                lab_id=lab_id,
            ).model_dump(mode="json")
        return res


    @tool(args_schema=ReservationCreateRequest)
    @handle_tool_errors
    def create_reservation_tool(
        runtime: ToolRuntime[UserContext],
        lab_id: int,
        equipment_id: int,
        reserve_date: date,
        start_time: time,
        end_time: time,
        remark: Optional[str] = None,
    ):
        """为当前用户创建一条设备预约记录。

        当用户明确表达"预约/预订某实验室的某设备,在某个日期和时间段"时使用。
        调用前应确认 lab_id、equipment_id、日期、起止时间均已明确,缺失时先向用户询问。
        在所有参数明确后，再次向确认是否预约。

        参数:
            lab_id: 实验室 ID
            equipment_id: 设备 ID
            reserve_date: 预约日期,格式 YYYY-MM-DD,例如 "2026-10-20"。
            start_time: 开始时间,格式 HH:MM,24 小时制,例如 "09:00"。
            end_time: 结束时间,格式 HH:MM,24 小时制,例如 "11:00",需晚于开始时间。
            remark: 备注,字符串,可选,例如用途说明。
        """


        data = ReservationCreateRequest(
            lab_id=lab_id,
            equipment_id=equipment_id,
            reserve_date=reserve_date,
            start_time=start_time,
            end_time=end_time,
            remark=remark,
        )

        with runtime.context.db_lock:
            create_reservation(
                runtime.context.db, runtime.context.current_user, data
            )
        return "预约已提交成功"


    @tool
    def get_today_datetime() -> str:
        """获取当前日期,格式 YYYY-MM-DD。

        当用户提到"今天/现在/本周"等相对时间,或创建预约需要确定今天的日期时先调用此工具,
        再结合结果计算预约日期。返回值为日期字符串,例如 "2026-10-19"。
        """
        return datetime.strftime(datetime.today(), "%Y-%m-%d")

    return (
        retrieve_tool,
        get_lab_data_tool,
        get_equipment_data_tool,
        create_reservation_tool,
        get_today_datetime,
    )
