"""用户接口模块."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User, UserRole
from src.security.jwt import get_current_user, require_admin

router = APIRouter()


class UserResponse(BaseModel):
    """用户响应模型."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool


class UserListResponse(BaseModel):
    """用户列表响应模型."""

    total: int
    users: list[UserResponse]


class UserUpdateRequest(BaseModel):
    """用户更新请求模型."""

    role: str | None = None
    is_active: bool | None = None


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """获取用户列表接口.

    - admin: 返回所有用户列表
    - 其他角色: 只返回自己的信息

    Args:
        current_user: 当前用户信息（从 JWT 解码）
        db: 数据库会话

    Returns:
        用户列表，包含总数
    """
    # admin 可查看所有用户，其他角色只查看自己
    if current_user.get("role") == "admin":
        result = await db.execute(select(User))
        users = result.scalars().all()
    else:
        result = await db.execute(
            select(User).where(User.id == current_user["user_id"])
        )
        users = result.scalars().all()

    user_list = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=str(user.role),
            is_active=user.is_active,
        )
        for user in users
    ]

    return UserListResponse(total=len(user_list), users=user_list)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """更新用户信息接口（仅 admin 可访问）.

    只能修改 role 和 is_active 字段。

    Args:
        user_id: 要更新的用户ID
        update_data: 更新数据
        current_user: 当前用户信息（需为 admin）
        db: 数据库会话

    Returns:
        更新后的用户信息
    """
    # 查询目标用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 防止 admin 修改自己的角色（避免无法恢复）
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能修改自己的信息")

    # 更新字段
    if update_data.role is not None:
        # 验证 role 值是否合法
        try:
            UserRole(update_data.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色值")
        user.role = UserRole(update_data.role)

    if update_data.is_active is not None:
        user.is_active = update_data.is_active

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=str(user.role),
        is_active=user.is_active,
    )
