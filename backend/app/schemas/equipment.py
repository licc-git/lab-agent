from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

class EquipmentBase(BaseModel):

    lab_id: int = Field(gt=0, description="所属实验室 ID")
    name: str = Field(min_length=1, max_length=64, description="设备名称")
    description: Optional[str] = Field(None, max_length=512, description="说明")
    img: Optional[str] = Field(None, max_length=256, description="图片")
    spec: Optional[str] = Field(None, max_length=128, description="型号规格")
    quantity: int = Field(1, ge=1, description="数量，最小为 1")
    status: Literal[0, 1] = Field(1, description="状态：0-维修，1-正常")


class EquipmentCreateRequest(EquipmentBase):
    pass


class EquipmentUpdateRequest(BaseModel):

    lab_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=512)
    img: Optional[str] = Field(None, max_length=256)
    spec: Optional[str] = Field(None, max_length=128)
    quantity: Optional[int] = Field(None, ge=1)
    status: Optional[Literal[0, 1]] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "EquipmentUpdateRequest":
        if self.model_dump(exclude_unset=True, exclude_none=True) == {}:
            raise ValueError("更新请求至少包含一个字段")
        return self


class EquipmentDeleteListRequest(BaseModel):
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


class EquipmentResponse(EquipmentBase):

    id: int
    lab_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EquipmentListResponse(BaseModel):
    data: list[EquipmentResponse]
    total: int
