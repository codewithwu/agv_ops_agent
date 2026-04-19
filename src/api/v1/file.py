"""文件上传接口."""

import hashlib
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.file import File as FileModel
from src.security.jwt import get_current_user, require_admin
from src.tasks import cleanup_physical_file
from src.tasks.submitter import submit_vectorize_task
from src.config import settings

router = APIRouter()

# 文件存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class FileResponse(BaseModel):
    """文件响应模型."""

    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    description: str | None
    created_at: str
    is_duplicate: bool = False  # 是否是重复文件
    user_id: int  # 上传者用户ID


class FileListResponse(BaseModel):
    """文件列表响应模型."""

    total: int
    files: list[FileResponse]


@router.post(
    "/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str | None = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """上传文件接口.

    相同文件（MD5 哈希相同）只会上传一次。
    支持的文件类型（.pdf, .md, .txt）会自动向量化。

    Args:
        file: 上传的文件
        description: 文件描述（可选）
        current_user: 当前用户信息
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        上传成功的文件信息，如果是重复文件则返回已存在的文件
    """
    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 计算文件 MD5 哈希
    file_hash = hashlib.md5(content).hexdigest()

    # 检查是否已存在相同文件
    result = await db.execute(select(FileModel).where(FileModel.file_hash == file_hash))
    existing_file = result.scalar_one_or_none()

    if existing_file:
        # 返回已存在的文件
        return FileResponse(
            id=existing_file.id,
            filename=existing_file.filename,
            original_filename=existing_file.original_filename,
            file_size=existing_file.file_size,
            mime_type=existing_file.mime_type,
            description=existing_file.description,
            created_at=existing_file.created_at.isoformat(),
            is_duplicate=True,
            user_id=existing_file.user_id,
        )

    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}",
        )

    # 创建文件记录
    file_record = FileModel(
        file_hash=file_hash,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        description=description,
        user_id=current_user["user_id"],
    )

    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # 文件扩展名检查并添加向量化后台任务
    file_ext = Path(file.filename).suffix.lower()
    if file_ext in settings.vectorizable_extensions:
        metadata = {
            "user_id": current_user["user_id"],
            "file_id": file_record.id,
            "original_filename": file.filename,
        }
        submit_vectorize_task(str(file_path), metadata, background_tasks)

    return FileResponse(
        id=file_record.id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_size=file_record.file_size,
        mime_type=file_record.mime_type,
        description=file_record.description,
        created_at=file_record.created_at.isoformat(),
        is_duplicate=False,
        user_id=file_record.user_id,
    )


@router.get("/files", response_model=FileListResponse)
async def list_files(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileListResponse:
    """获取文件列表.

    - admin: 查看所有用户上传的文件
    - 非 admin: 仅查看自己上传的文件

    Args:
        current_user: 当前用户信息
        db: 数据库会话

    Returns:
        文件列表
    """
    # admin 查看所有文件，非 admin 仅查看自己的文件
    if current_user.get("role") == "admin":
        result = await db.execute(
            select(FileModel).order_by(FileModel.created_at.desc())
        )
    else:
        result = await db.execute(
            select(FileModel)
            .where(FileModel.user_id == current_user["user_id"])
            .order_by(FileModel.created_at.desc())
        )
    files = result.scalars().all()

    file_list = [
        FileResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_size=f.file_size,
            mime_type=f.mime_type,
            description=f.description,
            created_at=f.created_at.isoformat(),
            user_id=f.user_id,
        )
        for f in files
    ]

    return FileListResponse(total=len(file_list), files=file_list)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除文件.

    Args:
        file_id: 文件ID
        background_tasks: 后台任务
        current_user: 当前用户信息
        db: 数据库会话
    """
    # 查询文件
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user["user_id"],
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )

    # 保存物理文件路径，用于后台删除
    file_path = file_record.file_path

    # 删除数据库记录
    await db.delete(file_record)
    await db.commit()

    # 物理文件删除交给后台任务
    background_tasks.add_task(cleanup_physical_file, file_path)
