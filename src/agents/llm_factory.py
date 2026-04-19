"""LLM 工厂模块.

提供不同 Provider 的 LLM 实例：
- Ollama (本地部署)
- OpenAI (云服务)
"""

from functools import lru_cache
from typing import Annotated, Any

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from src.config import settings


def _create_llm(provider: str) -> Any:
    """创建 LLM 实例.

    Args:
        provider: LLM 提供者

    Returns:
        LLM 实例
    """
    if provider == "ollama":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model_name,
            temperature=0.7,
        )
    elif provider == "openai":
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model_name,
            temperature=0.7,
        )
    else:
        raise ValueError(f"不支持的 LLM 提供者: {provider}")


@lru_cache()
def get_llm(
    llm_provider: Annotated[str, "LLM 提供者: 'ollama' 或 'openai'"] = "ollama",
) -> Any:
    """获取 LLM 实例（单例）.

    Args:
        llm_provider: LLM 提供者

    Returns:
        LLM 实例
    """
    return _create_llm(llm_provider)
