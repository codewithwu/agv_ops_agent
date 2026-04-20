"""RAG 代理模块.

基于 LangGraph 的 RAG Agent实现：
- 检索向量数据库获取相关文档
- 使用 LLM 生成答案
- 支持多轮对话记忆
"""

from typing import Annotated

from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from src.agents.llm_factory import get_llm
from src.services.vectorstore import get_vectorstore_service
from src.utils import console_logger


# 创建内存检查点（用于记忆存储）
checkpointer = InMemorySaver()

# RAG Agent 系统提示词
RAG_SYSTEM_PROMPT = """你是一个 AGV 智能助手。**你必须先调用 vector_search 工具检索相关文档，才能回答用户问题。**

规则：
1. 用户提问时，**必须先使用 vector_search 进行检索**
2. 根据检索结果回答，如果检索不到相关信息，直接告知用户
3. 禁止在没有检索的情况下自行编造答案

请用中文回答。"""


@tool
def vector_search(query: str) -> str:
    """根据用户问题，从 AGV 知识库中检索相关内容。

    当用户询问 AGV 操作、维护、故障处理等问题时，必须调用此工具检索文档。

        Args:
            query: 用户的问题描述，例如"AGV无法启动怎么办"、"手动模式怎么用"

        Returns:
            相关文档内容列表
    """
    console_logger.info(f"调用知识库检索工具，查询内容: {query}")

    vectorstore_service = get_vectorstore_service(
        embedding_provider="ollama",
        collection_name="agv_docs",
    )
    vs = vectorstore_service.get_vectorstore()
    results = vs.similarity_search(query=query, k=5)

    if not results:
        console_logger.info("知识库检索结果为空")
        return "没有找到相关文档"

    console_logger.info(f"知识库检索到 {len(results)} 条相关文档")

    # 格式化结果
    formatted_results = []
    for i, doc in enumerate(results, 1):
        formatted_results.append(
            f"文档 {i}:\n{doc.page_content}\n来源: {doc.metadata.get('original_filename', 'unknown')}"
        )
    return "\n\n".join(formatted_results)


def create_rag_agent(
    llm_provider: Annotated[str, "LLM 提供者: 'ollama' 或 'openai'"] = "openai",
):
    """创建带记忆功能的 RAG Agent.

    Args:
        llm_provider: LLM 提供者

    Returns:
        RAG Agent 实例（带记忆）
    """
    # 获取 LLM
    llm = get_llm(llm_provider)

    # 创建 Agent（带记忆功能）
    agent = create_agent(
        model=llm,
        tools=[vector_search],
        system_prompt=RAG_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent
