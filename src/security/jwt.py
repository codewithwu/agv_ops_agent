"""JWT 令牌工具模块."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings

# HTTP Bearer 安全方案
security = HTTPBearer()

# JWT 黑名单集合（生产环境应使用 Redis 存储）
_jwt_blacklist: set[str] = set()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT 访问令牌.

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 令牌过期时间增量，默认为配置中的值

    Returns:
        编码后的 JWT 令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建 JWT 刷新令牌.

    Args:
        data: 要编码到令牌中的数据

    Returns:
        编码后的刷新令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """验证 JWT 令牌.

    Args:
        token: JWT 令牌字符串

    Returns:
        解码后的数据字典，验证失败返回 None
    """
    # 检查令牌是否在黑名单中
    if token in _jwt_blacklist:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def blacklist_token(token: str) -> None:
    """将令牌加入黑名单.

    Args:
        token: JWT 令牌字符串
    """
    _jwt_blacklist.add(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """获取当前登录用户（依赖注入）.

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        解码后的用户信息

    Raises:
        HTTPException: 令牌无效或已过期
    """
    from fastapi import HTTPException

    payload = verify_token(credentials.credentials)

    if payload is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")

    return payload


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """要求用户具有管理员角色（依赖注入）.

    Args:
        current_user: 当前登录用户

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不是管理员
    """
    from fastapi import HTTPException

    from src.utils import console_logger

    console_logger.info(f"当前登录用户角色: {current_user.get('role')}")

    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限",
        )

    return current_user
