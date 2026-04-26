"""Agent State 模块.

定义 agent 持久化状态结构。
"""

from langchain.agents import AgentState as BaseAgentState
from typing import NotRequired


class AgentState(BaseAgentState):
    """Agent 持久化状态（跨请求保持）.

    继承自 AgentState，添加自定义持久化字段。
    """

    user_role: NotRequired[str | None] = None
