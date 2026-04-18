"""文件上传接口测试."""

import hashlib
import io
import pytest
from httpx import AsyncClient

from src.models.user import User, UserRole


def create_test_file(content: str = "test content") -> io.BytesIO:
    """创建测试文件."""
    return io.BytesIO(content.encode())


def get_file_hash(content: str) -> str:
    """计算文件 MD5 哈希."""
    return hashlib.md5(content.encode()).hexdigest()


async def register_admin_user(client: AsyncClient) -> str:
    """注册并返回 admin 用户的 token."""
    # 注册 admin 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "adminuser",
            "email": "admin@test.com",
            "password": "password123",
        },
    )

    # 登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "adminuser", "password": "password123"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_file_success(client: AsyncClient, db_session) -> None:
    """测试文件上传成功（admin 用户）."""
    from sqlalchemy import select

    # 注册 admin 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "adminuser",
            "email": "admin@test.com",
            "password": "password123",
        },
    )

    # 将用户角色改为 admin（需要在登录之前）
    result = await db_session.execute(select(User).where(User.username == "adminuser"))
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    # 登录获取 token（此时 token 会包含 admin role）
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "adminuser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 上传文件
    file_content = "AGV test file content"
    file = create_test_file(file_content)
    response = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.md", file, "text/markdown")},
        data={"description": "测试文件"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test.md"
    assert data["is_duplicate"] is False


@pytest.mark.asyncio
async def test_upload_duplicate_file(client: AsyncClient, db_session) -> None:
    """测试重复文件检测."""
    from sqlalchemy import select

    # 注册 admin 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dup@test.com",
            "password": "password123",
        },
    )

    # 将用户角色改为 admin（需要在登录之前）
    result = await db_session.execute(select(User).where(User.username == "dupuser"))
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    # 登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "dupuser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 第一次上传
    file_content = "duplicate test content"
    file1 = create_test_file(file_content)
    resp1 = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("dup.md", file1, "text/markdown")},
    )
    assert resp1.status_code == 201
    assert resp1.json()["is_duplicate"] is False

    # 第二次上传相同内容文件
    file2 = create_test_file(file_content)
    resp2 = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("dup2.md", file2, "text/markdown")},
    )
    assert resp2.status_code == 201
    assert resp2.json()["is_duplicate"] is True
    # 返回的是同一个文件
    assert resp1.json()["id"] == resp2.json()["id"]


@pytest.mark.asyncio
async def test_upload_file_without_auth(client: AsyncClient) -> None:
    """测试未认证上传文件."""
    file = create_test_file("test content")
    response = await client.post(
        "/api/v1/files/upload",
        files={"file": ("test.md", file, "text/markdown")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_file_non_admin_forbidden(client: AsyncClient) -> None:
    """测试非 admin 用户不能上传文件."""
    # 注册普通用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "normaluser",
            "email": "normal@test.com",
            "password": "password123",
        },
    )

    # 登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "normaluser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 尝试上传文件
    file = create_test_file("test content")
    response = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.md", file, "text/markdown")},
    )
    assert response.status_code == 403
    assert "需要管理员权限" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_files(client: AsyncClient) -> None:
    """测试获取文件列表."""
    # 注册用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "listuser",
            "email": "list@test.com",
            "password": "password123",
        },
    )

    # 登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "listuser", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 获取文件列表
    response = await client.get(
        "/api/v1/files/files",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "files" in data
    assert isinstance(data["files"], list)


@pytest.mark.asyncio
async def test_list_files_without_auth(client: AsyncClient) -> None:
    """测试未认证获取文件列表."""
    response = await client.get("/api/v1/files/files")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_file_admin_only(client: AsyncClient, db_session) -> None:
    """测试只有 admin 可以删除文件."""
    from sqlalchemy import select

    # 注册 admin 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_del",
            "email": "admin_del@test.com",
            "password": "password123",
        },
    )

    # 将 admin 用户角色改为 admin（需要在登录之前）
    result = await db_session.execute(select(User).where(User.username == "admin_del"))
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    # 注册普通用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "viewer_del",
            "email": "viewer_del@test.com",
            "password": "password123",
        },
    )

    # admin 登录并上传文件
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_del", "password": "password123"},
    )
    admin_token = admin_login.json()["access_token"]

    file = create_test_file("content to delete")
    upload_resp = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("todelete.md", file, "text/markdown")},
    )
    file_id = upload_resp.json()["id"]

    # viewer 用户尝试删除
    viewer_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "viewer_del", "password": "password123"},
    )
    viewer_token = viewer_login.json()["access_token"]

    delete_resp = await client.delete(
        f"/api/v1/files/files/{file_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert delete_resp.status_code == 403

    # admin 用户删除
    delete_resp = await client.delete(
        f"/api/v1/files/files/{file_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_file_not_found(client: AsyncClient, db_session) -> None:
    """测试删除不存在的文件."""
    from sqlalchemy import select

    # 注册 admin 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "del_notfound",
            "email": "del_notfound@test.com",
            "password": "password123",
        },
    )

    # 将用户角色改为 admin（需要在登录之前）
    result = await db_session.execute(
        select(User).where(User.username == "del_notfound")
    )
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    # 登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "del_notfound", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 尝试删除不存在的文件
    response = await client.delete(
        "/api/v1/files/files/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ============ 文件列表权限测试 ============


@pytest.mark.asyncio
async def test_list_files_admin_sees_all(client: AsyncClient, db_session) -> None:
    """测试 admin 查看所有用户（包括自己）上传的文件."""
    from sqlalchemy import select

    # 注册 admin1 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_list_all_1",
            "email": "admin_list_all_1@test.com",
            "password": "password123",
        },
    )
    result = await db_session.execute(
        select(User).where(User.username == "admin_list_all_1")
    )
    admin1_user = result.scalar_one()
    admin1_user.role = UserRole.ADMIN
    await db_session.commit()

    # 注册 admin2 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_list_all_2",
            "email": "admin_list_all_2@test.com",
            "password": "password123",
        },
    )
    result = await db_session.execute(
        select(User).where(User.username == "admin_list_all_2")
    )
    admin2_user = result.scalar_one()
    admin2_user.role = UserRole.ADMIN
    await db_session.commit()

    # admin1 登录
    admin1_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_list_all_1", "password": "password123"},
    )
    admin1_token = admin1_login.json()["access_token"]

    # admin2 登录
    admin2_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_list_all_2", "password": "password123"},
    )
    admin2_token = admin2_login.json()["access_token"]

    # admin1 上传文件
    file1 = create_test_file("admin1 file content")
    await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {admin1_token}"},
        files={"file": ("admin1_file.txt", file1, "text/plain")},
    )

    # admin2 上传文件
    file2 = create_test_file("admin2 file content")
    await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {admin2_token}"},
        files={"file": ("admin2_file.txt", file2, "text/plain")},
    )

    # admin1 查看文件列表 - 应该能看到所有用户的文件（包括 admin2 的）
    response = await client.get(
        "/api/v1/files/files",
        headers={"Authorization": f"Bearer {admin1_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["files"]) == 2
    # 验证返回的文件包含两个 admin 上传的文件
    filenames = [f["original_filename"] for f in data["files"]]
    assert "admin1_file.txt" in filenames
    assert "admin2_file.txt" in filenames


@pytest.mark.asyncio
async def test_list_files_non_admin_sees_own(client: AsyncClient, db_session) -> None:
    """测试非 admin 只能查看自己上传的文件（无文件时返回空列表）."""
    from sqlalchemy import select

    # 注册 operator 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "operator_sees_own",
            "email": "op_sees_own@test.com",
            "password": "password123",
        },
    )
    result = await db_session.execute(
        select(User).where(User.username == "operator_sees_own")
    )
    op_user = result.scalar_one()
    op_user.role = UserRole.OPERATOR
    await db_session.commit()

    # operator 登录
    op_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "operator_sees_own", "password": "password123"},
    )
    op_token = op_login.json()["access_token"]

    # operator 尝试上传文件 - 应该被拒绝（只有 admin 可以上传）
    file = create_test_file("operator content")
    upload_resp = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {op_token}"},
        files={"file": ("operator_file.txt", file, "text/plain")},
    )
    assert upload_resp.status_code == 403  # 非 admin 不能上传

    # operator 查看文件列表 - 因为从未上传过文件，应该返回空列表
    response = await client.get(
        "/api/v1/files/files",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["files"] == []


@pytest.mark.asyncio
async def test_delete_file_not_owner_fail(client: AsyncClient, db_session) -> None:
    """测试 admin 不能删除其他 admin 上传的文件（只能删除自己的）."""
    from sqlalchemy import select

    # 注册 admin1 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_owner_1",
            "email": "admin_owner_1@test.com",
            "password": "password123",
        },
    )
    result = await db_session.execute(
        select(User).where(User.username == "admin_owner_1")
    )
    admin1_user = result.scalar_one()
    admin1_user.role = UserRole.ADMIN
    await db_session.commit()

    # 注册 admin2 用户
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_owner_2",
            "email": "admin_owner_2@test.com",
            "password": "password123",
        },
    )
    result = await db_session.execute(
        select(User).where(User.username == "admin_owner_2")
    )
    admin2_user = result.scalar_one()
    admin2_user.role = UserRole.ADMIN
    await db_session.commit()

    # admin1 登录
    admin1_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_owner_1", "password": "password123"},
    )
    admin1_token = admin1_login.json()["access_token"]

    # admin2 登录
    admin2_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_owner_2", "password": "password123"},
    )
    admin2_token = admin2_login.json()["access_token"]

    # admin1 上传文件
    file = create_test_file("admin1 exclusive content")
    upload_resp = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {admin1_token}"},
        files={"file": ("admin1_file.txt", file, "text/plain")},
    )
    file_id = upload_resp.json()["id"]

    # admin2 尝试删除 admin1 的文件 - 应该失败（只能删除自己的）
    delete_resp = await client.delete(
        f"/api/v1/files/files/{file_id}",
        headers={"Authorization": f"Bearer {admin2_token}"},
    )
    assert delete_resp.status_code == 404
