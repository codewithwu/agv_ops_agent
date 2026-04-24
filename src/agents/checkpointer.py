"""Checkpointer 持久化模块.

基于 PostgreSQL 的 LangGraph checkpointer 实现：
- 懒加载连接池
- 自动创建必要的表
- 支持跨进程/重启持久化记忆
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from src.config import settings
from src.utils import console_logger


# 连接池和 checkpointer 实例（单例）
_pool: ConnectionPool | None = None
_checkpointer: PostgresSaver | None = None
_setup_done: bool = False


def get_checkpointer() -> PostgresSaver:
    """获取或创建 PostgresSaver 实例（懒加载）.

    首次调用时创建连接池并 setup 表，后续调用返回同一实例。

    Returns:
        PostgresSaver 实例
    """
    global _checkpointer, _pool, _setup_done
    if _checkpointer is None:
        _pool = ConnectionPool(
            settings.database_url_sync,
            min_size=4,
            max_size=10,
            open=True,
        )
        _checkpointer = PostgresSaver(_pool)

        # setup 必须在 autocommit 模式下执行（CREATE INDEX CONCURRENTLY 需要）
        # 只在首次创建时执行，之后复用已有表结构
        if not _setup_done:
            with _pool.connection() as conn:
                conn.autocommit = True
                _checkpointer.setup()
            _setup_done = True
            console_logger.info("PostgresSaver 数据库表初始化完成")

        console_logger.info("PostgresSaver 连接池已就绪")

    return _checkpointer
