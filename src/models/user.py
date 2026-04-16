"""User model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


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
    # 是否激活
    is_active: Mapped[bool] = mapped_column(default=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
