"""RAG Agent 工具模块."""

from langchain_core.tools import tool

from src.services.vectorstore import get_vectorstore_service
from src.utils import console_logger


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
