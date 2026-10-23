import os
import time
import uuid
import shutil

from fastapi import APIRouter, File, UploadFile
from pathlib import Path

from app.common.exceptions import BusinessException
from app.common.response import Response
from app.schemas.file import FileResponse
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload")
def upload(file: UploadFile):
    """文件上传的接口"""
    if not file.filename:
        raise BusinessException(message="文件名不能为空")

    orignal_name = os.path.basename(file.filename)
    ext = Path(orignal_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(message=f"不自持的文件后缀：{ext}")
    if file.size and file.size > MAX_FILE_SIZE:
        raise BusinessException(
            message=f"文件不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    disk_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = UPLOAD_DIR / disk_name
    with open(save_path, "wb") as f:
        shutil.copyfileobj(
            file.file, f, length=1024*1024
        )  # 源文件对象 → 目标文件对象，边读边写，每次搬 1MB

    return Response.success(
        data=FileResponse.model_validate({
            "original_name": orignal_name,
            "disk_name": disk_name,
            "size": file.size,
            "url": f"/uploads/{disk_name}",
        })
    )
