from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Annotated, Optional
from datetime import date, time, datetime
from app.common.enums import ReservationStatus


class ReservationCreateRequest(BaseModel):

    lab_id: Annotated[int, Field(ge=1, le=100, description="实验室ID")]
    equipment_id: Annotated[Optional[int], Field(None, ge=1, le=1000, description="设备ID")]
    reserve_date: Annotated[date, Field(..., description="预约日期")]
    start_time: Annotated[time, Field(..., description="预约开始时间")]
    end_time: Annotated[time, Field(..., description="预约结束时间")]
    remark: Annotated[Optional[str], Field(None, max_length=64, description="备注")]

    @field_validator("reserve_date")
    @classmethod
    def validate_date(cls, value):
        if value < date.today():
            raise ValueError("预约日期不能小于当前日期")
        return value

    @model_validator(mode="after")
    def check_schedule(self):
        if self.reserve_date == date.today() and self.start_time < datetime.now().time():
            raise ValueError("预约日期不能小于当前时间")

        if self.end_time <= self.start_time:
            raise ValueError("预约结束时间必须晚于开始时间")
        return self

    model_config = ConfigDict(
        str_strip_whitespace=True,  # 自动去除字符串首尾空格
        json_schema_extra={
            "examples": [
                {
                    "lab_id": 1,
                    "equipment_id": 3,
                    "reserve_date": "2026-10-15",
                    "start_time": "09:00:00",
                    "end_time": "11:30:00",
                    "remark": "做材料拉伸实验",
                }
            ]
        },
    )


class ReservationStatusAudit(BaseModel):
    status: ReservationStatus


class ReservationResponse(BaseModel):

    id: int
    user_name: str
    reserve_type: str
    lab_name: str
    equipment_name: Optional[str] = None
    reserve_date: date
    start_time: time
    end_time: time
    remark: Optional[str] = None
    status: ReservationStatus

    model_config = ConfigDict(from_attributes=True)

class ReservationListResponse(BaseModel):

    data: list[ReservationResponse]
    total: int
