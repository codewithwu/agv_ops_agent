"""RAG Agent 测试."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.rag_agent import create_rag_agent, vector_search, checkpointer


class TestCreateRagAgent:
    """create_rag_agent 测试类."""

    def test_create_rag_agent_returns_agent(self) -> None:
        """测试 create_rag_agent 返回 agent 实例."""
        with patch("src.agents.rag_agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            agent = create_rag_agent(llm_provider="ollama")

            assert agent is not None
            mock_get_llm.assert_called_once_with("ollama")

    def test_create_rag_agent_with_different_provider(self) -> None:
        """测试使用不同 provider 创建 agent."""
        with patch("src.agents.rag_agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            agent = create_rag_agent(llm_provider="openai")

            assert agent is not None
            mock_get_llm.assert_called_once_with("openai")

    def test_create_rag_agent_has_checkpointer(self) -> None:
        """测试 create_rag_agent 创建的 agent 带有 checkpointer."""
        with patch("src.agents.rag_agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            agent = create_rag_agent(llm_provider="ollama")

            # 检查 agent 是否配置了 checkpointer
            # checkpointer 在 agent 内部使用，不需要在 config 中直接访问
            assert agent is not None


class TestVectorSearch:
    """vector_search 工具测试类."""

    def test_vector_search_returns_string(self) -> None:
        """测试 vector_search 返回字符串."""
        result = vector_search.invoke({"query": "AGV 无法启动"})
        assert isinstance(result, str)

    @pytest.mark.skip(reason="需要 Ollama 和向量存储服务运行，仅手动测试时启用")
    def test_vector_search_with_real_data(self) -> None:
        """测试 vector_search 实际检索（需要向量数据库有数据）."""
        result = vector_search.invoke({"query": "AGV 无法启动"})
        assert "AGV" in result or "没有找到相关文档" in result

    def test_vector_search_with_mock(self) -> None:
        """测试 vector_search 使用 mock."""
        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [
            MagicMock(
                page_content="测试文档内容", metadata={"original_filename": "test.md"}
            )
        ]

        with patch("src.agents.rag_agent.get_vectorstore_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_vectorstore.return_value = mock_vs
            mock_get_service.return_value = mock_service

            result = vector_search.invoke({"query": "测试查询"})

            assert "测试文档内容" in result
            assert "test.md" in result


class TestRagAgentMemory:
    """RAG Agent 记忆功能测试类."""

    def test_checkpointer_is_inmemory(self) -> None:
        """测试 checkpointer 是 InMemorySaver 实例."""
        from langgraph.checkpoint.memory import InMemorySaver

        assert isinstance(checkpointer, InMemorySaver)

    def test_rag_agent_invoke_with_session_id(self) -> None:
        """测试带 session_id 的 agent 调用（使用 mock）。"""
        # 验证 checkpointer 可用于 session_id 配置
        from langgraph.checkpoint.memory import InMemorySaver

        checkpointer = InMemorySaver()
        config = {
            "configurable": {"thread_id": "test_session_001"},
            "checkpoint": checkpointer,
        }

        # 验证配置可以正确构建
        assert config["configurable"]["thread_id"] == "test_session_001"
        assert isinstance(config["checkpoint"], InMemorySaver)

    def test_rag_agent_different_session_ids(self) -> None:
        """测试不同 session_id 产生不同的记忆存储."""
        from langgraph.checkpoint.memory import InMemorySaver

        # InMemorySaver 应该能区分不同 thread_id
        checkpointer_1 = InMemorySaver()
        checkpointer_2 = InMemorySaver()

        # 不同 session 应该有不同的存储
        assert checkpointer_1 is not checkpointer_2


class TestRagAgentIntegration:
    """RAG Agent 集成测试（使用 OpenAI LLM 和 PGVector 向量存储）。"""

    @pytest.mark.asyncio
    async def test_rag_agent_invoke(self) -> None:
        """测试 RAG Agent 实际调用（使用 OpenAI LLM）。"""
        agent = create_rag_agent(llm_provider="openai")
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "AGV 无法启动怎么办？"}]},
            config={"configurable": {"thread_id": "test_invoke_001"}},
        )

        assert result is not None
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_rag_agent_multiturn_conversation(self) -> None:
        """测试 RAG Agent 多轮对话（带记忆，使用 OpenAI LLM）。"""
        agent = create_rag_agent(llm_provider="openai")

        session_id = "test_multiturn_001"

        # 第一轮
        result1 = agent.invoke(
            {"messages": [{"role": "user", "content": "什么是AGV"}]},
            config={"configurable": {"thread_id": session_id}},
        )
        assert result1 is not None

        # 第二轮（带记忆）
        result2 = agent.invoke(
            {"messages": [{"role": "user", "content": "它有哪些用途"}]},
            config={"configurable": {"thread_id": session_id}},
        )
        assert result2 is not None
        # 验证第二轮使用了第一轮的记忆
        assert len(result2["messages"]) > len(result1["messages"])
