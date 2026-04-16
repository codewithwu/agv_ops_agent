"""密码哈希工具模块."""

import bcrypt


def hash_password(password: str) -> str:
    """对密码进行哈希处理.

    Args:
        password: 原始密码

    Returns:
        哈希后的密码字符串
    """
    # 将密码编码为字节并进行哈希处理
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配.

    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
