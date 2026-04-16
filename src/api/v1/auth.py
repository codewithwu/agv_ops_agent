"""认证接口模块."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.security.jwt import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    security,
)
from src.security.password import hash_password, verify_password

router = APIRouter()


# 用户注册请求模型
class RegisterRequest(BaseModel):
    """注册请求模型."""

    username: str  # 用户名，3-20字符
    email: EmailStr  # 邮箱
    password: str  # 密码，6-50字符


class RegisterResponse(BaseModel):
    """注册响应模型."""

    id: int
    username: str
    email: str


# 用户登录请求模型
class LoginRequest(BaseModel):
    """登录请求模型."""

    username: str  # 用户名
    password: str  # 密码


class LoginResponse(BaseModel):
    """登录响应模型."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 访问令牌过期时间（秒）


# 刷新令牌请求模型
class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


# 修改密码请求模型
class ChangePasswordRequest(BaseModel):
    """修改密码请求模型."""

    old_password: str  # 旧密码
    new_password: str  # 新密码，6-50字符


class ChangePasswordResponse(BaseModel):
    """修改密码响应模型."""

    message: str


# JWT 黑名单集合（生产环境应使用 Redis）
_jwt_blacklist: set[str] = set()


def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中.

    Args:
        token: JWT 令牌

    Returns:
        是否在黑名单中
    """
    return token in _jwt_blacklist


def blacklist_token(token: str) -> None:
    """将令牌加入黑名单（退出登录）.

    Args:
        token: JWT 令牌
    """
    _jwt_blacklist.add(token)


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """用户注册接口.

    Args:
        request: 注册请求，包含用户名、邮箱和密码
        db: 数据库会话

    Returns:
        新创建的用户信息

    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    # 验证密码长度
    if len(request.password) < 6 or len(request.password) > 50:
        raise HTTPException(status_code=400, detail="密码长度必须在6-50字符之间")

    # 验证用户名长度
    if len(request.username) < 3 or len(request.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度必须在3-20字符之间")

    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == request.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == request.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建新用户
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RegisterResponse(
        id=new_user.id, username=new_user.username, email=new_user.email
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """用户登录接口.

    Args:
        request: 登录请求，包含用户名和密码
        db: 数据库会话

    Returns:
        JWT 访问令牌

    Raises:
        HTTPException: 用户名或密码错误
    """
    # 查找用户
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    # 验证密码
    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 创建访问令牌
    expires_delta = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=expires_delta,
    )

    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """刷新访问令牌接口.

    使用刷新令牌获取新的访问令牌。

    Args:
        request: 刷新令牌请求，包含刷新令牌
        db: 数据库会话

    Returns:
        新的访问令牌

    Raises:
        HTTPException: 刷新令牌无效或已过期
    """
    from src.security.jwt import verify_token

    # 验证刷新令牌
    payload = verify_token(request.refresh_token)

    if payload is None:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    # 检查令牌类型
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    # 获取用户信息
    user_id = payload.get("user_id")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 创建新的访问令牌
    expires_delta = timedelta(minutes=30)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=expires_delta,
    )

    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
    )


@router.post("/logout", status_code=200)
async def logout(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """用户退出登录接口.

    将当前令牌加入黑名单，使令牌失效。

    Args:
        current_user: 当前用户信息（从 JWT 解码）
        credentials: HTTP Bearer 凭证

    Returns:
        退出成功消息
    """
    from src.security.jwt import blacklist_token

    # 将令牌加入黑名单
    blacklist_token(credentials.credentials)
    return {"message": "退出成功"}


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChangePasswordResponse:
    """修改密码接口.

    Args:
        request: 修改密码请求，包含旧密码和新密码
        current_user: 当前用户信息（从 JWT 解码）
        db: 数据库会话

    Returns:
        修改成功消息

    Raises:
        HTTPException: 旧密码错误或新密码格式不正确
    """
    # 验证新密码长度
    if len(request.new_password) < 6 or len(request.new_password) > 50:
        raise HTTPException(status_code=400, detail="新密码长度必须在6-50字符之间")

    # 获取当前用户
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证旧密码
    if not verify_password(request.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="旧密码错误")

    # 更新密码
    user.hashed_password = hash_password(request.new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()

    return ChangePasswordResponse(message="密码修改成功")


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取当前登录用户信息.

    Args:
        current_user: 当前用户信息（从 JWT 解码）
        db: 数据库会话

    Returns:
        用户信息
    """
    # 获取最新用户信息
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
