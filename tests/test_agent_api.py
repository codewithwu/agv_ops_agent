"""智能体问答接口测试."""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from src.models.user import User, UserRole


async def register_and_login(
    client: AsyncClient, db_session, username: str = "agentuser"
) -> str:
    """注册用户并登录，返回 token."""
    # 注册用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "password123",
        },
    )

    # 将用户角色改为 admin
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    # 登录
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_chat_without_auth(client: AsyncClient) -> None:
    """测试未认证访问 /chat 接口."""
    response = await client.post(
        "/api/v1/agent/chat",
        json={"message": "AGV无法启动怎么办？"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_success(client: AsyncClient, db_session) -> None:
    """测试 /chat 接口成功调用（使用 mock）。"""
    token = await register_and_login(client, db_session, "chat_user_001")

    with patch("src.api.v1.agent.create_rag_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_result = {
            "messages": [
                MagicMock(content="这是测试回答"),
            ]
        }
        mock_agent.invoke.return_value = mock_result
        mock_create_agent.return_value = mock_agent

        response = await client.post(
            "/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "AGV无法启动怎么办？",
                "session_id": "test_session_001",
                "llm_provider": "openai",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data
        assert "messages" in data
        assert data["session_id"] == "test_session_001"


@pytest.mark.asyncio
async def test_chat_with_default_session_id(client: AsyncClient, db_session) -> None:
    """测试 /chat 接口使用默认 session_id（使用 mock）。"""
    token = await register_and_login(client, db_session, "chat_user_002")

    with patch("src.api.v1.agent.create_rag_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_result = {
            "messages": [
                MagicMock(content="默认会话回答"),
            ]
        }
        mock_agent.invoke.return_value = mock_result
        mock_create_agent.return_value = mock_agent

        response = await client.post(
            "/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "什么是AGV"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "default"


@pytest.mark.asyncio
async def test_chat_request_validation(client: AsyncClient, db_session) -> None:
    """测试 /chat 请求参数验证."""
    token = await register_and_login(client, db_session, "chat_user_003")

    # 缺少 message 字段
    response = await client.post(
        "/api/v1/agent/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_ollama_provider(client: AsyncClient, db_session) -> None:
    """测试使用 ollama provider（使用 mock）。"""
    token = await register_and_login(client, db_session, "chat_user_004")

    with patch("src.api.v1.agent.create_rag_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_result = {
            "messages": [
                MagicMock(content="Ollama 回答"),
            ]
        }
        mock_agent.invoke.return_value = mock_result
        mock_create_agent.return_value = mock_agent

        response = await client.post(
            "/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "AGV无法启动怎么办？",
                "llm_provider": "ollama",
            },
        )

        assert response.status_code == 200
        # 验证 create_rag_agent 被调用时使用了 ollama
        mock_create_agent.assert_called_once_with(llm_provider="ollama")


@pytest.mark.asyncio
async def test_chat_stream_without_auth(client: AsyncClient) -> None:
    """测试未认证访问 /chat/stream 接口."""
    response = await client.post(
        "/api/v1/agent/chat/stream",
        json={"message": "AGV无法启动怎么办？"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_stream_success(client: AsyncClient, db_session) -> None:
    """测试 /chat/stream 接口成功调用（使用 mock）。"""
    token = await register_and_login(client, db_session, "stream_user_001")

    with patch("src.api.v1.agent.create_rag_agent") as mock_create_agent:
        mock_agent = MagicMock()

        # 模拟同步 generator（langchain agent.stream 是同步的）
        def mock_stream(*args, **kwargs):
            messages = [
                MagicMock(content="这是"),
                MagicMock(content="测试"),
                MagicMock(content="回答"),
            ]
            for msg in messages:
                yield msg, {"stream_mode": "messages"}

        mock_agent.stream = MagicMock(return_value=mock_stream())
        mock_create_agent.return_value = mock_agent

        response = await client.post(
            "/api/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "AGV无法启动怎么办？",
                "session_id": "test_stream_session",
                "llm_provider": "openai",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # 读取流式内容
        content = b""
        async for chunk in response.aiter_bytes():
            content += chunk
        decoded = content.decode("utf-8")
        assert "这是" in decoded
        assert "测试" in decoded
        assert "回答" in decoded


@pytest.mark.asyncio
async def test_chat_stream_with_ollama_provider(
    client: AsyncClient, db_session
) -> None:
    """测试使用 ollama provider（使用 mock）。"""
    token = await register_and_login(client, db_session, "stream_user_002")

    with patch("src.api.v1.agent.create_rag_agent") as mock_create_agent:
        mock_agent = MagicMock()

        def mock_stream(*args, **kwargs):
            yield MagicMock(content="Ollama 流式回答"), {"stream_mode": "messages"}

        mock_agent.stream = MagicMock(return_value=mock_stream())
        mock_create_agent.return_value = mock_agent

        response = await client.post(
            "/api/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "什么是AGV",
                "llm_provider": "ollama",
            },
        )

        assert response.status_code == 200

        content = b""
        async for chunk in response.aiter_bytes():
            content += chunk
        decoded = content.decode("utf-8")
        assert "Ollama 流式回答" in decoded

        # 验证 create_rag_agent 被调用时使用了 ollama
        mock_create_agent.assert_called_once_with(llm_provider="ollama")


@pytest.mark.asyncio
async def test_chat_stream_request_validation(client: AsyncClient, db_session) -> None:
    """测试 /chat/stream 请求参数验证."""
    token = await register_and_login(client, db_session, "stream_user_003")

    # 缺少 message 字段
    response = await client.post(
        "/api/v1/agent/chat/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 422  # Validation error
