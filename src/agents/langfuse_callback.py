"""LangFuse 回调模块.

用于追踪 agent 的调用记录。
"""

import langfuse

from src.config import settings
from src.utils import console_logger as logger


def observe_agent(func):
    """LangFuse observe 装饰器（用于 agent 调用）.

    用法:
        @observe_agent
        async def chat():
            return agent.invoke(...)

    Args:
        func: 被装饰的函数
    """
    # 如果未配置 LangFuse，直接返回原函数
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.info("LangFuse 未配置，跳过追踪")
        return func

    # 使用 langfuse.observe 装饰器
    logger.info(
        f"LangFuse 追踪已启用 - base_url: {settings.langfuse_base_url}, "
        f"public_key: {settings.langfuse_public_key[:15]}..."
    )
    return langfuse.observe(as_type="agent", name=func.__name__)(func)
