"""LLM 工厂模块测试."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.llm_factory import get_llm, _create_llm


class TestGetLlm:
    """get_llm 测试类."""

    def test_get_llm_returns_ollama_llm(self) -> None:
        """测试 get_llm 返回 Ollama LLM 实例."""
        get_llm.cache_clear()
        llm = get_llm(llm_provider="ollama")
        assert llm is not None
        assert "qwen3.5" in str(llm.model)

    def test_get_llm_returns_openai_llm(self) -> None:
        """测试 get_llm 返回 OpenAI LLM 实例（使用 mock）."""
        with patch("src.agents.llm_factory.ChatOpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance

            get_llm.cache_clear()
            llm = get_llm(llm_provider="openai")

            assert llm is not None
            mock_openai.assert_called_once()
        get_llm.cache_clear()

    def test_invalid_llm_provider(self) -> None:
        """测试无效的 LLM 提供者."""
        with pytest.raises(ValueError, match="不支持的 LLM 提供者"):
            _create_llm("invalid_provider")

    def test_get_llm_singleton(self) -> None:
        """测试 get_llm 返回相同实例."""
        get_llm.cache_clear()
        llm1 = get_llm(llm_provider="ollama")
        llm2 = get_llm(llm_provider="ollama")
        assert llm1 is llm2
        get_llm.cache_clear()

    def test_get_llm_different_providers(self) -> None:
        """测试不同 provider 返回不同实例."""
        get_llm.cache_clear()
        llm1 = get_llm(llm_provider="ollama")
        get_llm.cache_clear()
        llm2 = get_llm(llm_provider="openai")
        assert llm1 is not llm2
        get_llm.cache_clear()

    def test_llm_invoke_with_mock(self) -> None:
        """测试 LLM 调用（使用 mock）."""
        from langchain_ollama import ChatOllama

        mock_response = MagicMock()
        mock_response.content = "这是测试回答"

        with patch.object(ChatOllama, "invoke", return_value=mock_response):
            get_llm.cache_clear()
            llm = get_llm(llm_provider="ollama")
            messages = [{"role": "user", "content": "你好"}]
            response = llm.invoke(messages)

            assert response.content == "这是测试回答"
        get_llm.cache_clear()


class TestLlmIntegration:
    """集成测试（需要 Ollama 服务运行）."""

    @pytest.mark.skip(reason="需要 Ollama 服务运行，仅手动测试时启用")
    @pytest.mark.asyncio
    async def test_ollama_llm_call(self) -> None:
        """测试 Ollama LLM 实际调用（需要本地 Ollama 服务）."""
        get_llm.cache_clear()
        llm = get_llm(llm_provider="ollama")
        messages = [{"role": "user", "content": "1+1等于几？"}]
        response = llm.invoke(messages)
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.skip(reason="需要 OpenAI API 配置，仅手动测试时启用")
    @pytest.mark.asyncio
    async def test_openai_llm_call(self) -> None:
        """测试 OpenAI LLM 实际调用（需要 API 配置）."""
        get_llm.cache_clear()
        llm = get_llm(llm_provider="openai")
        messages = [{"role": "user", "content": "1+1等于几？"}]
        response = llm.invoke(messages)
        assert response.content is not None
        assert len(response.content) > 0
