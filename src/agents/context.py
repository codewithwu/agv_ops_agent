"""Agent Context 模块.

定义 agent 运行时的上下文结构。
"""

from typing import TypedDict


class AgentContext(TypedDict):
    """Agent 运行时上下文.

    Attributes:
        user_id: 用户 ID
    """

    user_id: str
