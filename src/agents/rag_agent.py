"""RAG Agent 模块.

基于 LangGraph 的 RAG Agent 实现：
- 检索向量数据库获取相关文档
- 使用 LLM 生成答案
- 支持多轮对话记忆（持久化到 PostgreSQL）
- 支持多例模式，相同 session_id 复用同一 agent 实例
"""

from typing import Annotated, Any

from langchain.agents import create_agent

from src.agents.checkpointer import get_checkpointer
from src.agents.context import AgentContext
from src.agents.state import AgentState
from src.agents.llm_factory import get_llm
from src.agents.middleware import get_all_middleware
from src.agents.store import get_store
from src.agents.tools import get_all_tools
from src.utils import console_logger


class AgentManager:
    """Agent 多例管理器（单例）.

    相同 session_id 复用同一 agent 实例，避免重复创建。
    """

    _instance: "AgentManager | None" = None
    _agents: dict[str, Any] = {}  # session_id → agent

    def __new__(cls) -> "AgentManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._agents = {}
        return cls._instance

    def get_agent(
        self,
        session_id: Annotated[str, "会话 ID"],
        llm_provider: Annotated[str, "LLM 提供者: 'ollama' 或 'openai'"] = "openai",
    ) -> Any:
        """获取或创建 agent 实例.

        Args:
            session_id: 会话 ID，相同 session_id 返回同一 agent 实例
            llm_provider: LLM 提供者

        Returns:
            RAG Agent 实例（带记忆）
        """
        if session_id not in self._agents:
            llm = get_llm(llm_provider)
            self._agents[session_id] = create_agent(
                model=llm,
                tools=get_all_tools(),
                checkpointer=get_checkpointer(),
                store=get_store(),
                state_schema=AgentState,
                context_schema=AgentContext,
                middleware=get_all_middleware(),
            )
            console_logger.info(
                f"创建新 Agent 实例，session_id: {session_id}, "
                f"agent_id: {id(self._agents[session_id])}, "
                f"当前实例总数: {len(self._agents)}"
            )
        else:
            console_logger.info(
                f"复用已有 Agent 实例，session_id: {session_id}, "
                f"agent_id: {id(self._agents[session_id])}, "
                f"当前实例总数: {len(self._agents)}"
            )
        return self._agents[session_id]

    def clear_session(self, session_id: str) -> None:
        """清理指定会话的 agent 实例.

        Args:
            session_id: 要清理的会话 ID
        """
        if session_id in self._agents:
            del self._agents[session_id]
            console_logger.info(f"已清理会话 agent: {session_id}")

    def clear_all(self) -> None:
        """清理所有 agent 实例."""
        self._agents.clear()
        console_logger.info("已清理所有会话 agent")

    @property
    def active_sessions(self) -> list[str]:
        """获取当前活跃的会话 ID 列表."""
        return list(self._agents.keys())
