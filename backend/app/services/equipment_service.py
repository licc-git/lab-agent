from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.common.exceptions import BusinessException
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.schemas.equipment import (
    EquipmentResponse,
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
    EquipmentListResponse,
)

# 允许置空（清空）的字段：对应 ORM 中 Optional[str] 可空列
NULLABLE_FIELDS = {"description", "img", "spec"}


def _to_response(equipment: Equipment) -> EquipmentResponse:
    """统一转换：lab 已通过 selectinload 预加载，这里不会触发额外 SQL"""
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def get_equipment_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: Optional[str] = None,
    lab_id: Optional[int] = None,
) -> EquipmentListResponse:
    """分页模糊查询列表"""
    query = db.query(Equipment).options(selectinload(Equipment.lab))
    # 生成的 SQL：
    # SELECT * FROM equipments LIMIT 20;
    # SELECT * FROM labs WHERE labs.id IN (1,2,3,...);

    if lab_id is not None:
        query = query.filter(Equipment.lab_id == lab_id)
    if keywords:
        kw = f"%{keywords}%"
        # 名称或型号命中即返回
        query = query.filter(Equipment.name.ilike(kw) | Equipment.spec.ilike(kw))

    total = query.count()
    items = (
        query.order_by(Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return EquipmentListResponse(
        data=[_to_response(item) for item in items], total=total
    )


def _ensure_lab_exists(db: Session, lab_id: int) -> None:
    if not db.query(Lab.id).filter(Lab.id == lab_id).first():
        raise BusinessException(message="实验室不存在")


def create_equipment(db: Session, data: EquipmentCreateRequest) -> EquipmentResponse:
    """新增"""
    exist = (
        db.query(Equipment.id)
        .filter(
            Equipment.lab_id == data.lab_id,
            Equipment.name == data.name,
        )
        .first()
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")

    _ensure_lab_exists(db, data.lab_id)

    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment, ["lab"])
    return _to_response(equipment)


def update_equipment(
    db: Session, equipment_id: int, data: EquipmentUpdateRequest
) -> EquipmentResponse:
    """更新"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="实验室设备不存在")

    payload = data.model_dump(exclude_unset=True)
    # 过滤非法 null：仅可空字段允许显式置空，其余 null 剔除
    payload = {
        k: v for k, v in payload.items() if v is not None or k in NULLABLE_FIELDS
    }
    if not payload:
        raise BusinessException(message="更新内容不能为空")

    # 只在 lab_id/name 真正变更时才做校验（避免无用查询）
    new_lab_id: int = payload.get("lab_id", equipment.lab_id) # type: ignore
    new_name = payload.get("name", equipment.name)
    need_check = "lab_id" in payload or "name" in payload

    if need_check:
        if "lab_id" in payload:
            _ensure_lab_exists(db, new_lab_id)
        if new_name != equipment.name or new_lab_id != equipment.lab_id:
            exist = (
                db.query(Equipment.id)
                .filter(
                    Equipment.lab_id == new_lab_id,
                    Equipment.name == new_name,
                    Equipment.id != equipment.id,
                )
                .first()
            )
            if exist:
                raise BusinessException(message="同一个实验室不能存在同名的设备")

    for field, value in payload.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment, ["lab"])
    return _to_response(equipment)


def delete_equipment(db: Session, equipment_id: int) -> None:
    """删除"""
    deleted = db.query(Equipment).filter(Equipment.id == equipment_id).delete()
    db.commit()
    if not deleted:
        raise BusinessException(message="实验室设备不存在")


def delete_equipments(db: Session, ids: list[int]) -> int:
    """批量删除，返回实际删除条数"""
    deleted = (
        db.query(Equipment)
        .filter(Equipment.id.in_(ids))
        .delete(synchronize_session=False)  # 不用管内存，直接发 SQL 删除，优化性能
    )
    db.commit()
    return deleted
