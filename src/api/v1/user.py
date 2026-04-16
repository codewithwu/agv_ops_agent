"""用户接口模块."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.security.jwt import get_current_user

router = APIRouter()


class UserResponse(BaseModel):
    """用户响应模型."""

    id: int
    username: str
    email: str
    is_active: bool


class UserListResponse(BaseModel):
    """用户列表响应模型."""

    total: int
    users: list[UserResponse]


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """获取所有用户列表接口.

    Args:
        current_user: 当前用户信息（从 JWT 解码）
        db: 数据库会话

    Returns:
        用户列表，包含总数
    """
    # 查询所有用户
    result = await db.execute(select(User))
    users = result.scalars().all()

    user_list = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )
        for user in users
    ]

    return UserListResponse(total=len(user_list), users=user_list)
