"""File model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class File(Base):
    """File table - 用户上传文件."""

    __tablename__ = "files"

    # 主键自增ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 文件哈希（MD5，用于去重）
    file_hash: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    # 文件名
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # 原始文件名
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # 文件路径
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    # 文件大小（字节）
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    # MIME 类型
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # 文件描述
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 上传用户ID（外键）
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="files")
