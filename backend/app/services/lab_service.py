from app.common.exceptions import BusinessException
from app.utils.common import escape_like
from app.models import Lab
from app.schemas.lab import (
    LabResponse,
    LabListResponse,
    LabCreateRequest,
    LabUpdateRequest,
)

from sqlalchemy import or_
from sqlalchemy.orm import Session


def get_lab_page_list(
    db: Session,
    page: int,
    page_size: int,
    status: int | None = None,
    keywords: str | None = None,
):
    query = db.query(Lab)
    if keywords:
        query = query.filter(
            or_(
                Lab.name.ilike(f"%{escape_like(keywords)}%"),
                Lab.location.ilike(f"%{escape_like(keywords)}%"),
            )
        )
    if status is not None:
        query = query.filter(Lab.status == status)
    total = query.count()
    if total < 1:
        raise BusinessException("未查询到实验室数据")
    items = (
        query.order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return LabListResponse(
        data=[LabResponse.model_validate(item) for item in items],
        total=total,
    )


def get_lab_detail(db: Session, lab_id: int):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    return LabResponse.model_validate(lab)


def get_lab_options(db: Session):
    """下拉选项专用：只取 id + name，不分页无上限"""
    return [
        {"id": id, "name": name}
        for id, name in db.query(Lab.id, Lab.name).order_by(Lab.id).all()
    ]


def create_lab(db: Session, data: LabCreateRequest):
    exists = db.query(Lab).filter(Lab.name == data.name).first()
    if exists:
        raise BusinessException(message="实验室名称已存在")

    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateRequest):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    payload = data.model_dump(exclude_none=True)
    if "name" in payload and payload["name"] != lab.name:
        exists = (
            db.query(Lab).filter(Lab.name == payload["name"], Lab.id != lab_id).first()
        )
        if exists:
            raise BusinessException(message="实验室名称已存在")

    for field, value in payload.items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db: Session, lab_id: int):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    db.delete(lab)
    db.commit()


def delete_labs(db: Session, ids: list[int]) -> int:
    """批量删除，返回实际删除条数"""
    deleted = (
        db.query(Lab)
        .filter(Lab.id.in_(ids))
        .delete(synchronize_session=False)  # 不用管内存，直接发 SQL 删除，优化性能
    )
    db.commit()
    return deleted
