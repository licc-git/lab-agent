import inspect
import json

from sqlalchemy.orm import Session
from app.services.lab_service import get_lab_page_list
from app.services.equipment_service import get_equipment_page_list

# 告诉LLM现在已有的tools
TOOLS: list = [
    {
        "type": "function",
        "function": {
            "name": "get_lab_page_list",
            "description": "查询所有（或某个）实验室的信息列表（前10个）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "实验室的名字/位置"},
                    "status": {
                        "type": "integer",
                        "description": "实验室状态：开放/关闭",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_equipment_page_list",
            "description": "查询所有（或某个）设备的信息列表（前10个）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "设备的名称/型号"},
                    "lab_id": {"type": "integer", "description": "实验室的ID"},
                },
            },
        },
    },
]


def _call_with_supported_kwargs(fn, db, page, page_size, status, lab_id, keywords):
    """传入函数的参数过滤和解析"""
    sign = inspect.signature(fn)
    params = sign.parameters

    pool = {
        "db": db,
        "page": page,
        "page_size": page_size,
        "status": status,
        "lab_id": lab_id,
        "keywords": keywords,
    }

    call_kwargs = {}
    for name, p in params.items():
        # 跳过 *args / **kwargs 本身
        if p.kind in (p.VAR_KEYWORD, p.VAR_POSITIONAL):
            continue
        if name in pool:
            call_kwargs[name] = pool[name]
        elif p.default is p.empty:
            raise TypeError(f"{fn.__name__} 缺少必填参数 {name}")

    return fn(**call_kwargs)


def run_tool(db: Session, func: str, arguments: str):
    """调用LLM需要的工具并返回结果"""
    func_dict = {
        "get_lab_page_list": get_lab_page_list,
        "get_equipment_page_list": get_equipment_page_list,
    }
    tool = func.strip()
    if tool not in func_dict:
        return "抱歉，未查到相关信息"
    if arguments.strip():
        try:
            args: dict = json.loads(arguments)
            keywords = args.get("keywords")
            status = args.get("status")
            lab_id = args.get("lab_id")
        except:
            status, lab_id, keywords = None, None, None
    else:
        status, lab_id, keywords = None, None, None

    res = _call_with_supported_kwargs(
        fn=func_dict[tool],
        db=db,
        page=1,
        page_size=10,
        status=status,
        lab_id=lab_id,
        keywords=keywords,
    )

    return res.model_dump(mode="json")
