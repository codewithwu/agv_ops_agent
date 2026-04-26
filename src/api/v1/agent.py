"""智能体问答接口."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agents.rag_agent import AgentManager
from src.security.jwt import get_current_user
from src.utils import console_logger

router = APIRouter()


class ChatRequest(BaseModel):
    """对话请求模型."""

    message: str
    session_id: str = "default"
    llm_provider: str = "openai"


class ChatResponse(BaseModel):
    """对话响应模型."""

    message: str
    session_id: str
    messages: list[dict]


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """RAG 智能问答流式输出接口.

    Args:
        request: 对话请求，包含消息、会话ID和大模型提供商
        current_user: 当前用户信息

    Returns:
        流式响应，逐块输出 AI 回复内容
    """
    console_logger.info(f"流式对话请求，会话: {request.session_id}")

    # 通过 AgentManager 获取 Agent（多例模式，相同 session_id 复用实例）
    agent_manager = AgentManager()
    agent = agent_manager.get_agent(
        session_id=request.session_id, llm_provider=request.llm_provider
    )
    console_logger.info(f"current_user: {current_user}")

    async def generate():
        """异步生成流式响应."""
        try:
            for token, metadata in agent.stream(
                {"messages": [{"role": "user", "content": request.message}]},
                config={"configurable": {"thread_id": request.session_id}},
                context={
                    "user_id": current_user.get("sub", "anonymous"),
                    "user_role": current_user.get("role", "viewer"),
                },
                stream_mode="messages",
            ):
                # 检查 token 是否有 content 属性
                if hasattr(token, "content") and token.content:
                    content = token.content
                    console_logger.debug(f"流式输出: {content}")
                    yield content
        except Exception as e:
            console_logger.error(f"流式输出异常: {e}")
            yield f"[错误: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    """RAG 智能问答（支持多轮对话记忆）.

    Args:
        request: 对话请求，包含消息、会话ID和大模型提供商
        current_user: 当前用户信息

    Returns:
        对话结果
    """
    # 通过 AgentManager 获取 Agent（多例模式，相同 session_id 复用实例）
    agent_manager = AgentManager()
    agent = agent_manager.get_agent(
        session_id=request.session_id, llm_provider=request.llm_provider
    )

    # 调用 Agent
    result = agent.invoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": request.session_id}},
        context={
            "user_id": current_user.get("sub", "anonymous"),
            "user_role": current_user.get("role", "viewer"),
        },
    )

    # 提取回复消息
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        reply = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )
    else:
        reply = "无法获取回复"

    return ChatResponse(
        message=reply,
        session_id=request.session_id,
        messages=[
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ],
    )
