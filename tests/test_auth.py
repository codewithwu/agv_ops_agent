"""认证接口测试."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """测试注册成功."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    """测试用户名重复注册."""
    # 先注册一个用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "first@example.com",
            "password": "password123",
        },
    )

    # 尝试用相同用户名注册
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    """测试无效邮箱格式."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123",
        },
    )
    assert response.status_code == 422  # Pydantic 验证失败


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    """测试密码过短."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
        },
    )
    assert response.status_code == 400
    assert "密码长度必须在6-50字符之间" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_username(client: AsyncClient) -> None:
    """测试用户名过短."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "ab",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "用户名长度必须在3-20字符之间" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """测试登录成功."""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
        },
    )

    # 登录
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """测试密码错误."""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "password123",
        },
    )

    # 错误密码登录
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "wrongpass",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient) -> None:
    """测试用户不存在."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123",
        },
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient) -> None:
    """测试获取当前用户信息成功."""
    # 先注册并登录
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "meuser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 获取当前用户
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["email"] == "me@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient) -> None:
    """测试无令牌访问."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401  # HTTPBearer 返回 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient) -> None:
    """测试无效令牌访问."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    assert "令牌无效或已过期" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient) -> None:
    """测试刷新令牌成功."""
    # 先注册并登录
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "refreshuser", "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # 使用刷新令牌获取新访问令牌
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """测试无效刷新令牌."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_refresh_token"},
    )
    assert response.status_code == 401
    assert "刷新令牌无效或已过期" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient) -> None:
    """测试修改密码成功."""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "changepwd",
            "email": "changepwd@example.com",
            "password": "oldpassword",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "changepwd", "password": "oldpassword"},
    )
    token = login_resp.json()["access_token"]

    # 修改密码
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "oldpassword", "new_password": "newpassword123"},
    )
    assert response.status_code == 200
    assert "密码修改成功" in response.json()["message"]

    # 用新密码登录
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "changepwd", "password": "newpassword123"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(client: AsyncClient) -> None:
    """测试旧密码错误."""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongoldpwd",
            "email": "wrongold@example.com",
            "password": "correctpassword",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongoldpwd", "password": "correctpassword"},
    )
    token = login_resp.json()["access_token"]

    # 旧密码错误
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "wrongpassword", "new_password": "newpassword123"},
    )
    assert response.status_code == 401
    assert "旧密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient) -> None:
    """测试退出登录成功."""
    # 先注册并登录
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "logoutuser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 退出登录
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "退出成功" in response.json()["message"]

    # 尝试用旧令牌访问，应该失败
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 401
