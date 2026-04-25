from functools import lru_cache

from langchain.agents.middleware import (
    SummarizationMiddleware,
    before_model,
    after_model,
)
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from typing import Any


from src.utils.logger import console_logger as logger


class LoggingSummarizationMiddleware(SummarizationMiddleware):
    """带日志的摘要中间件.

    继承自 SummarizationMiddleware，在触发摘要时记录日志。
    """

    def before_model(
        self, state: AgentState[Any], runtime: Runtime[Any]
    ) -> dict[str, Any] | None:
        """在模型调用前执行，记录触发状态."""
        result = super().before_model(state, runtime)
        messages = state["messages"]
        if result is not None:
            logger.info(
                f"摘要中间件触发 - 消息数量: {len(messages)}, "
                f"触发阈值: 4000 tokens, 保留策略: 最近20条"
            )
        return result


def get_summarize_middleware() -> LoggingSummarizationMiddleware:
    """获取摘要中间件实例（懒加载）.

    当 token 达到 4000 时触发摘要，保留最近 20 条消息。
    使用项目中已有的 LLM 配置。
    """
    from src.agents.llm_factory import get_llm

    middleware = LoggingSummarizationMiddleware(
        model=get_llm("openai"),  # 复用已有的 LLM 配置
        trigger=("tokens", 4000),
        keep=("messages", 20),
    )
    logger.info("摘要中间件初始化成功")
    return middleware


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """保留最近的消息条数，以适应上下文窗口大小。"""
    messages = state["messages"]

    logger.info(f"trim_messages - 当前消息数量: {len(messages)}, messages: {messages}")

    if len(messages) <= 3:
        return None  # 无需修改

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}


@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    """只保留最后两条消息."""
    messages = state["messages"]
    logger.info(
        f"delete_old_messages - 当前消息数量: {len(messages)}, messages: {messages}"
    )
    if len(messages) > 2:
        # 只保留最后两条，删除前面的消息
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:-2]]}
    return None


# =============================================================================
# 中间件列表（懒加载）
# =============================================================================


@lru_cache
def get_all_middleware() -> list:
    """获取所有中间件列表（懒加载）."""
    return [
        # get_summarize_middleware(),
        # trim_messages,
        # delete_old_messages,
    ]
