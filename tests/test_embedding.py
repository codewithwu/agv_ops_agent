"""Embedding 服务测试."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.embedding import (
    OllamaEmbeddingsService,
    OpenAIEmbeddingsService,
    get_embedding_service,
)


class TestGetEmbeddingService:
    """get_embedding_service 测试."""

    def test_get_ollama_service(self) -> None:
        """测试获取 Ollama 服务."""
        with patch("src.services.embedding.OllamaEmbeddings"):
            service = get_embedding_service("ollama")
            assert isinstance(service, OllamaEmbeddingsService)

    def test_get_openai_service(self) -> None:
        """测试获取 OpenAI 服务."""
        with patch("src.services.embedding.OpenAIEmbeddings"):
            service = get_embedding_service("openai")
            assert isinstance(service, OpenAIEmbeddingsService)

    def test_invalid_provider(self) -> None:
        """测试无效 provider."""
        with pytest.raises(ValueError, match="不支持的 Provider"):
            get_embedding_service("invalid")

    def test_singleton_ollama(self) -> None:
        """测试 Ollama 单例模式."""
        with patch("src.services.embedding.OllamaEmbeddings"):
            s1 = get_embedding_service("ollama")
            s2 = get_embedding_service("ollama")
            assert s1 is s2

    def test_singleton_openai(self) -> None:
        """测试 OpenAI 单例模式."""
        with patch("src.services.embedding.OpenAIEmbeddings"):
            s1 = get_embedding_service("openai")
            s2 = get_embedding_service("openai")
            assert s1 is s2

    def test_different_provider_different_instance(self) -> None:
        """测试不同 provider 返回不同实例."""
        with (
            patch("src.services.embedding.OllamaEmbeddings"),
            patch("src.services.embedding.OpenAIEmbeddings"),
        ):
            ollama_service = get_embedding_service("ollama")
            openai_service = get_embedding_service("openai")
            assert ollama_service is not openai_service

    def test_lru_cache_clear_between_tests(self) -> None:
        """测试 lru_cache 在不同测试间正常工作.

        由于 lru_cache 是模块级缓存，需要确保测试隔离。
        这里验证缓存确实生效（同一 provider 返回同一实例）。
        """
        with patch("src.services.embedding.OllamaEmbeddings"):
            s1 = get_embedding_service("ollama")
            s2 = get_embedding_service("ollama")
            assert s1 is s2  # 缓存生效


class TestOllamaEmbeddingsService:
    """OllamaEmbeddingsService 测试."""

    def test_as_langchain_returns_ollama_embeddings(self) -> None:
        """测试 as_langchain 返回正确的 LangChain 实例."""
        with patch("src.services.embedding.OllamaEmbeddings") as MockOllama:
            mock_instance = MagicMock()
            MockOllama.return_value = mock_instance

            service = OllamaEmbeddingsService()
            result = service.as_langchain()

            assert result is mock_instance
            MockOllama.assert_called_once()


class TestOpenAIEmbeddingsService:
    """OpenAIEmbeddingsService 测试."""

    def test_as_langchain_returns_openai_embeddings(self) -> None:
        """测试 as_langchain 返回正确的 LangChain 实例."""
        with patch("src.services.embedding.OpenAIEmbeddings") as MockOpenAI:
            mock_instance = MagicMock()
            MockOpenAI.return_value = mock_instance

            service = OpenAIEmbeddingsService()
            result = service.as_langchain()

            assert result is mock_instance
            MockOpenAI.assert_called_once()
