from datetime import datetime, time
from enum import IntEnum
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


DEFAULT_OPEN_DAYS = [0, 1, 2, 3, 4]


class LabStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class LabBase(BaseModel):
    """公共字段与校验"""

    name: str = Field(..., min_length=1, max_length=20, description="实验室名称")
    location: str | None = Field(default=None, min_length=5, max_length=50)
    capacity: int | None = Field(default=0, ge=0, le=99, description="容纳人数")
    open_time: time | None = Field(default=None, description="每日开放开始时间")
    close_time: time | None = Field(default=None, description="每日开放结束时间")
    open_days: list[int] = Field(
        default_factory=lambda: DEFAULT_OPEN_DAYS.copy(),
        description="每周开放日，0为周一，6为周日",
    )
    description: str | None = Field(default=None, max_length=512)
    img: str | None = Field(default=None, max_length=256)
    status: int = Field(default=LabStatus.ENABLED, description="0-关闭 1-开放")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名称不能为空白字符")
        return v

    @field_validator("status")
    @classmethod
    def check_status(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("status 只能为 0（关闭）或 1（开放）")
        return v

    @field_validator("open_days")
    @classmethod
    def check_open_days(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("开放日必须是 0 到 6，0 表示周一")
        if len(value) != len(set(value)):
            raise ValueError("开放日不能重复")
        return sorted(value)

    @model_validator(mode="after")
    def check_schedule(self):
        if (self.open_time is None) != (self.close_time is None):
            raise ValueError("每日开放开始和结束时间必须同时填写")
        if self.open_time is not None and self.close_time is not None:
            if self.close_time <= self.open_time:
                raise ValueError("每日结束时间必须晚于开始时间")
        return self


class LabCreateRequest(LabBase):

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "计算机网络实验室",
                    "location": "教学楼 A 座 302",
                    "capacity": 40,
                    "open_time": "08:00",
                    "close_time": "22:00",
                    "open_days": [0, 1, 2, 3, 4],
                    "description": "配备 60 台高配主机",
                    "img": "https://xxx.com/lab1.png",
                    "status": 1,
                }
            ]
        }
    )


class LabUpdateRequest(BaseModel):

    name: str | None = Field(default=None, min_length=1, max_length=20)
    location: str | None = Field(default=None, min_length=5, max_length=50)
    capacity: int | None = Field(default=None, ge=0, le=99)
    open_time: time | None = None
    close_time: time | None = None
    open_days: list[int] | None = None
    description: str | None = Field(default=None, max_length=512)
    img: str | None = Field(default=None, max_length=256)
    status: int | None = None

    @field_validator("open_days")
    @classmethod
    def check_open_days(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("开放日必须是 0 到 6，0 表示周一")
        if len(value) != len(set(value)):
            raise ValueError("开放日不能重复")
        return sorted(value)

    @model_validator(mode="after")
    def check_schedule(self):
        schedule_fields = {"open_time", "close_time", "open_days"}
        supplied = self.model_fields_set
        if supplied & schedule_fields:
            if "open_time" not in supplied or "close_time" not in supplied:
                raise ValueError("更新开放时间时必须同时提供开始和结束时间")
            if self.open_days is None:
                raise ValueError("更新开放时间时必须提供每周开放日")
            if (self.open_time is None) != (self.close_time is None):
                raise ValueError("每日开放开始和结束时间必须同时填写")
            if self.open_time is not None and self.close_time is not None:
                if self.close_time <= self.open_time:
                    raise ValueError("每日结束时间必须晚于开始时间")
        return self


class LabDeleteListRequest(BaseModel):
    """批量删除实验室请求"""

    ids: list[int] = Field(
        ...,
        min_length=1,
        description="要删除的实验室 ID 列表",
        examples=[[1, 2, 3]],
    )

    @field_validator("ids")
    @classmethod
    def clean_ids(cls, v: list[int]) -> list[int]:
        v = list(set(v))
        v = [i for i in v if i > 0]
        if not v:
            raise ValueError("ids 不能为空，且必须为正整数")
        return v


class LabResponse(LabBase):

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LabListResponse(BaseModel):

    data: list[LabResponse]
    total: int
