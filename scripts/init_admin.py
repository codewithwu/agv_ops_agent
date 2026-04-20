#!/usr/bin/env python3
"""初始化管理员用户脚本."""

import argparse
import asyncio
import os

from sqlalchemy import select

from src.database import async_session_maker
from src.models.user import User, UserRole
from src.security.password import hash_password


async def create_admin_user(username: str, password: str) -> bool:
    """创建管理员用户.

    Args:
        username: 用户名
        password: 密码

    Returns:
        是否创建成功
    """
    async with async_session_maker() as db:
        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"用户 '{username}' 已存在")
            return False

        # 创建管理员用户
        new_user = User(
            username=username,
            email=f"{username}@admin.local",
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(new_user)
        await db.commit()
        print(f"管理员用户 '{username}' 创建成功")
        return True


def main():
    # 从环境变量读取默认配置
    default_username = os.getenv("TEST_ADMIN_USERNAME", "admin")
    default_password = os.getenv("TEST_ADMIN_PASSWORD", "admin123")

    parser = argparse.ArgumentParser(description="初始化管理员用户")
    parser.add_argument("--username", default=default_username, help="管理员用户名")
    parser.add_argument("--password", default=default_password, help="管理员密码")
    args = parser.parse_args()

    if len(args.password) < 6:
        print("错误：密码长度至少6个字符")
        return

    asyncio.run(create_admin_user(args.username, args.password))


if __name__ == "__main__":
    main()
