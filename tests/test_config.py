"""测试 config.py 配置模块."""

import os
from unittest.mock import patch


def test_config_loads_from_env_file():
    """验证 config 从 .env 文件加载配置."""
    from src.config import settings

    # 由于 .env 文件中有 database_url，验证是否正确加载
    assert (
        settings.database_url
        == "postgresql+asyncpg://postgres:123456@localhost:5432/app"
    )
    assert (
        settings.database_url_sync == "postgresql://postgres:123456@localhost:5432/app"
    )


def test_config_loads_from_env_variables():
    """验证 config 从环境变量加载配置（优先级高于 .env）."""
    env_vars = {
        "database_url": "postgresql+asyncpg://test:pass@localhost:5432/testdb",
        "database_url_sync": "postgresql://test:pass@localhost:5432/testdb",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        # 重新导入以读取新的环境变量
        import importlib
        import src.config

        importlib.reload(src.config)

        from src.config import settings

        assert (
            settings.database_url
            == "postgresql+asyncpg://test:pass@localhost:5432/testdb"
        )
        assert (
            settings.database_url_sync == "postgresql://test:pass@localhost:5432/testdb"
        )

        # 恢复原始配置
        importlib.reload(src.config)
