"""User model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.file import File


class UserRole(str, Enum):
    """用户角色枚举."""

    ADMIN = "admin"  # 管理员
    OPERATOR = "operator"  # 操作员
    VIEWER = "viewer"  # 普通查看者


class User(Base):
    """User table."""

    __tablename__ = "users"

    # 主键自增ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 用户名，唯一索引
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    # 邮箱，唯一索引
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    # 密码哈希值
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # 用户角色：admin=管理员, operator=操作员, viewer=查看者
    role: Mapped[UserRole] = mapped_column(
        String(20), default=UserRole.VIEWER, nullable=False
    )
    # 是否激活
    is_active: Mapped[bool] = mapped_column(default=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 一对多关联：用户上传的文件
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="user", cascade="all, delete-orphan"
    )
