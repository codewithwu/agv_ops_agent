"""Embedding 服务模块.

支持多种 Embedding Provider:
- ollama: 本地 Ollama 服务
- openai: OpenAI 或兼容 API（如 ModelScope）
"""

from functools import lru_cache

from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings

from src.config import settings


class OllamaEmbeddingsService:
    """Ollama Embedding 服务."""

    def __init__(self):
        self._embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model_name,
        )

    def as_langchain(self) -> OllamaEmbeddings:
        """返回 LangChain Embeddings 实例."""
        return self._embeddings


class OpenAIEmbeddingsService:
    """OpenAI/ModelScope Embedding 服务."""

    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            api_key=settings.openai_embedding_api_key,
            base_url=settings.openai_embedding_base_url,
            model=settings.openai_embedding_model_name,
        )

    def as_langchain(self) -> OpenAIEmbeddings:
        """返回 LangChain Embeddings 实例."""
        return self._embeddings


@lru_cache()
def get_embedding_service(
    provider: str = "ollama",
) -> OllamaEmbeddingsService | OpenAIEmbeddingsService:
    """获取 Embedding 服务实例（单例）.

    Args:
        provider: "ollama" 或 "openai"

    Returns:
        Embedding 服务实例
    """
    if provider == "ollama":
        return OllamaEmbeddingsService()
    elif provider == "openai":
        return OpenAIEmbeddingsService()
    else:
        raise ValueError(f"不支持的 Provider: {provider}")
