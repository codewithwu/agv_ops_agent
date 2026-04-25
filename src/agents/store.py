"""Agent Store 模块.

支持两种存储后端：
- InMemoryStore：内存存储，测试用
- PostgresStore：PostgreSQL 持久化存储，生产环境用
"""

import psycopg
from functools import lru_cache

from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore

from src.config import settings
from src.utils import console_logger

# ============================================================================
# 方式一：全局变量 + lazy init（主选）
# ============================================================================

# Store 实例（单例）
_store: PostgresStore | InMemoryStore | None = None
_pool_conn: psycopg.Connection | None = None
_setup_done: bool = False


def get_store() -> PostgresStore | InMemoryStore:
    """获取 Store 实例（单例）.

    根据配置选择存储后端：
    - database_url_sync 已配置：使用 PostgresStore
    - 否则使用 InMemoryStore（默认）
    """
    global _store, _pool_conn, _setup_done
    if _store is None:
        if settings.database_url_sync:
            _pool_conn = psycopg.connect(settings.database_url_sync)
            _pool_conn.autocommit = True
            _store = PostgresStore(_pool_conn)
            if not _setup_done:
                _store.setup()
                _setup_done = True
                console_logger.info("PostgresStore 表初始化完成")
            console_logger.info("Store 使用 PostgresStore")
        else:
            _store = InMemoryStore()
            console_logger.info("Store 使用 InMemoryStore（测试模式）")
    return _store


# ============================================================================
# 方式二：@lru_cache（备选）
# ============================================================================


@lru_cache
def get_store_cached() -> PostgresStore | InMemoryStore:
    """获取 Store 实例（单例）- @lru_cache 版本.

    备用实现，功能与 get_store() 相同。
    清除缓存：get_store_cached.cache_clear()
    """
    if settings.database_url_sync:
        conn = psycopg.connect(settings.database_url_sync)
        conn.autocommit = True
        store = PostgresStore(conn)
        store.setup()
        console_logger.info("PostgresStore 表初始化完成（cached）")
        console_logger.info("Store 使用 PostgresStore（cached）")
        return store
    else:
        console_logger.info("Store 使用 InMemoryStore（cached）")
        return InMemoryStore()


def clear_store_cache() -> None:
    """清除 get_store_cached 的缓存."""
    get_store_cached.cache_clear()
    console_logger.info("Store 缓存已清除")
