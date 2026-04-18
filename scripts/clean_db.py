#!/usr/bin/env python3
"""清空数据库中数据表的记录."""

import asyncio

from src.database import async_session_maker


async def clean_database():
    """清空数据库中的 files 和 users 表."""
    from sqlalchemy import text

    async with async_session_maker() as db:
        # 按顺序删除（files 有外键关联 users）
        await db.execute(text("DELETE FROM files"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()
        print("数据库记录已清空")


def main():
    print("警告：此操作将清空数据库中所有用户和文件记录！")
    confirm = input("确认执行？(y/N): ")
    if confirm.lower() != "y":
        print("已取消")
        return

    asyncio.run(clean_database())
    print("清理完成")


if __name__ == "__main__":
    main()
