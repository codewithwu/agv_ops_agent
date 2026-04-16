"""数据库连接和会话管理."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明性基类."""

    ...


# 异步数据库引擎
engine = create_async_engine(settings.database_url, echo=settings.debug)

# 异步会话制造器
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖项."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
