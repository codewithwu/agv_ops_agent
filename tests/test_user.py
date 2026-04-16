"""用户接口测试."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_success(client: AsyncClient) -> None:
    """测试获取用户列表成功."""
    # 先注册几个用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
        },
    )
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
        },
    )

    # 登录获取令牌
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "user1", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 获取用户列表
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "users" in data
    assert data["total"] >= 2
    assert len(data["users"]) >= 2


@pytest.mark.asyncio
async def test_list_users_without_token(client: AsyncClient) -> None:
    """测试无令牌访问."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401  # HTTPBearer 返回 401


@pytest.mark.asyncio
async def test_list_users_invalid_token(client: AsyncClient) -> None:
    """测试无效令牌访问."""
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    assert "令牌无效或已过期" in response.json()["detail"]
