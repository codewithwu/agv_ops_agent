"""智能体问答接口."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.agents.rag_agent import create_rag_agent
from src.security.jwt import get_current_user

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
    # 创建 Agent
    agent = create_rag_agent(llm_provider=request.llm_provider)

    # 调用 Agent
    result = agent.invoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": request.session_id}},
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
