"""RAG Agent 工具模块."""

from functools import lru_cache

from langchain.tools import tool, ToolRuntime

from src.services.vectorstore import get_vectorstore_service
from src.utils import console_logger


# =============================================================================
# Store 示例工具（展示 InMemoryStore 的用法）
# =============================================================================


@tool
def save_user_preference(
    runtime: ToolRuntime,
    preference_key: str,
    preference_value: str,
) -> str:
    """保存用户偏好设置到 Store.

    user_id 会自动从运行时上下文获取。

    Args:
        runtime: 工具运行时，包含上下文信息
        preference_key: 偏好键名，如 "language", "theme", "notification"
        preference_value: 偏好值

    Returns:
        保存结果信息
    """
    from src.agents.store import get_store

    user_id = runtime.context.get("user_id", "unknown")
    store = get_store()
    console_logger.info(f"store 1 {id(store)}")
    store.put(
        ("user_preference", user_id),
        preference_key,
        {"value": preference_value},
    )
    console_logger.info(
        f"保存用户偏好 - user_id: {user_id}, {preference_key}: {preference_value}"
    )
    return f"已保存用户偏好: {preference_key} = {preference_value}"


@tool
def get_user_preference(
    runtime: ToolRuntime,
    preference_key: str,
) -> str:
    """获取用户偏好设置.

    user_id 会自动从运行时上下文获取。

    Args:
        runtime: 工具运行时，包含上下文信息
        preference_key: 偏好键名

    Returns:
        偏好值，如果不存在返回提示
    """
    console_logger.info("调用 get_user_preference 工具")
    from src.agents.store import get_store

    user_id = runtime.context.get("user_id", "unknown")
    store = get_store()
    console_logger.info(f"store 2 {id(store)}")
    item = store.get(("user_preference", user_id), preference_key)
    console_logger.info(f"item 1 {item}")
    if item:
        value = item.value.get("value", "")
        console_logger.info(
            f"获取用户偏好 - user_id: {user_id}, {preference_key}: {value}"
        )
        return f"{preference_key} = {value}"
    console_logger.info(f"用户偏好不存在 - user_id: {user_id}, {preference_key}")
    return f"用户 {user_id} 的 {preference_key} 偏好未设置"


# =============================================================================
# RAG 相关工具
# =============================================================================


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


# =============================================================================
# 工具列表（懒加载）
# =============================================================================


@lru_cache
def get_all_tools() -> list:
    """获取所有工具列表（懒加载）."""
    return [
        # 用户偏好工具
        save_user_preference,
        get_user_preference,
        # RAG 工具
        vector_search,
    ]
