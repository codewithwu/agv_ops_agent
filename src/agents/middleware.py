from functools import lru_cache

from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    SummarizationMiddleware,
    before_model,
    after_model,
    wrap_model_call,
    wrap_tool_call,
    dynamic_prompt,
)
from langchain.messages import RemoveMessage, ToolMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from typing import Any


from src.utils.logger import console_logger as logger


class LoggingSummarizationMiddleware(SummarizationMiddleware):
    """带日志的摘要中间件.

    继承自 SummarizationMiddleware，在触发摘要时记录日志。
    """

    def before_model(
        self, state: AgentState[Any], runtime: Runtime[Any]
    ) -> dict[str, Any] | None:
        """在模型调用前执行，记录触发状态."""
        result = super().before_model(state, runtime)
        messages = state["messages"]
        if result is not None:
            logger.info(
                f"摘要中间件触发 - 消息数量: {len(messages)}, "
                f"触发阈值: 4000 tokens, 保留策略: 最近20条"
            )
        return result


def get_summarize_middleware() -> LoggingSummarizationMiddleware:
    """获取摘要中间件实例（懒加载）.

    当 token 达到 4000 时触发摘要，保留最近 20 条消息。
    使用项目中已有的 LLM 配置。
    """
    from src.agents.llm_factory import get_llm

    middleware = LoggingSummarizationMiddleware(
        model=get_llm("openai"),  # 复用已有的 LLM 配置
        trigger=("tokens", 4000),
        keep=("messages", 20),
    )
    logger.info("摘要中间件初始化成功")
    return middleware


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """保留最近的消息条数，以适应上下文窗口大小。"""
    messages = state["messages"]

    logger.info(f"trim_messages - 当前消息数量: {len(messages)}, messages: {messages}")

    if len(messages) <= 3:
        return None  # 无需修改

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}


@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    """只保留最后两条消息."""
    messages = state["messages"]
    logger.info(
        f"delete_old_messages - 当前消息数量: {len(messages)}, messages: {messages}"
    )
    if len(messages) > 2:
        # 只保留最后两条，删除前面的消息
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:-2]]}
    return None


# =============================================================================
# 角色权限中间件
# =============================================================================

# 工具权限配置（开放方案：所有角色可以使用所有工具）
TOOL_PERMISSIONS = {
    "admin": [],  # admin 拥有所有工具
    "operator": [],  # 操作员拥有所有工具
    "viewer": [],  # 查看者拥有所有工具（后续可根据需要限制）
}


@wrap_model_call
def role_based_tools(request: ModelRequest, handler) -> ModelResponse:
    """根据用户角色过滤工具.

    未认证用户（viewer）只能使用公开工具。
    操作员不能使用管理级工具。
    管理员可以使用所有工具。
    """
    # 从 runtime.context 直接获取 user_role（而非从 state）
    user_role = request.runtime.context.get("user_role", "viewer")
    logger.info(f"role_based_tools - 当前用户角色: {user_role}")

    # 获取该角色不能使用的工具
    forbidden_tools = TOOL_PERMISSIONS.get(user_role, [])

    # 过滤工具
    if forbidden_tools:
        original_count = len(request.tools)
        tools = [t for t in request.tools if t.name not in forbidden_tools]
        logger.info(
            f"role_based_tools - 过滤前工具数: {original_count}, "
            f"过滤后工具数: {len(tools)}, 禁用: {forbidden_tools}"
        )
        request = request.override(tools=tools)

    return handler(request)


# =============================================================================
# 动态提示词中间件
# =============================================================================


@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    """根据用户问题动态切换提示词.

    - AGV 相关问题：使用 RAG 提示词，引导检索知识库
    - 普通问题：使用普通助手提示词
    """
    from src.agents.prompts import (
        DEFAULT_SYSTEM_PROMPT,
        RAG_SYSTEM_PROMPT,
        is_agv_related,
    )

    # 获取用户最新消息
    messages = request.state.get("messages", [])
    if not messages:
        return DEFAULT_SYSTEM_PROMPT

    last_message = messages[-1]
    user_content = (
        last_message.content if hasattr(last_message, "content") else str(last_message)
    )

    # 判断是否 AGV 相关
    if is_agv_related(user_content):
        logger.info("检测到 AGV 相关问题，使用 RAG 提示词")
        return RAG_SYSTEM_PROMPT

    logger.info("普通问题，使用默认提示词")
    return DEFAULT_SYSTEM_PROMPT


# =============================================================================
# 工具错误处理中间件
# =============================================================================


@wrap_tool_call
def handle_tool_errors(request, handler):
    """处理工具执行异常.

    当工具执行发生错误时，返回友好的错误消息，而不是让整个流程崩溃。
    """
    try:
        logger.info("hello world 1")
        return handler(request)
    except Exception as e:
        logger.warning(f"工具执行失败: {request.tool_call.get('name')} - {e}")
        return ToolMessage(
            content=f"工具执行出错，请检查输入或稍后重试。({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


# =============================================================================
# 模型 fallback 中间件
# =============================================================================


@wrap_model_call
def model_fallback_middleware(request: ModelRequest, handler) -> ModelResponse:
    """主模型报错时切换到备用模型.

    当主模型调用发生任何错误时，自动切换到备用模型（ling）重试。
    """
    from src.agents.llm_factory import get_llm

    try:
        raise ValueError('test')
        return handler(request)
    except Exception as e:
        logger.warning(f"主模型调用失败，切换到备用模型: {e}")
        fallback_llm = get_llm("ling")
        return handler(request.override(model=fallback_llm))


# =============================================================================
# 中间件列表（懒加载）
# =============================================================================


@lru_cache
def get_all_middleware() -> list:
    """获取所有中间件列表（懒加载）."""
    return [
        dynamic_system_prompt,  # 动态切换提示词
        role_based_tools,  # 根据角色过滤工具
        model_fallback_middleware,  # 模型失败时切换备用模型
        handle_tool_errors,  # 工具执行异常处理
    ]
