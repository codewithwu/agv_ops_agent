"""安全模块测试."""

from src.security.jwt import create_access_token, create_refresh_token, verify_token
from src.security.password import hash_password, verify_password


class TestPassword:
    """密码工具测试."""

    def test_hash_password(self) -> None:
        """测试密码哈希."""
        password = "testpassword123"
        hashed = hash_password(password)

        # 哈希后的密码不应等于原密码
        assert hashed != password
        # 哈希应该以 $2 开头 (bcrypt 格式)
        assert hashed.startswith("$2")

    def test_verify_password_correct(self) -> None:
        """测试正确密码验证."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """测试错误密码验证."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self) -> None:
        """测试相同密码生成不同哈希."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # bcrypt 每次生成不同的 salt，所以哈希不同
        assert hash1 != hash2
        # 但都能验证通过
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWT:
    """JWT 工具测试."""

    def test_create_access_token(self) -> None:
        """测试创建访问令牌."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self) -> None:
        """测试创建刷新令牌."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self) -> None:
        """测试验证令牌成功."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 1
        assert payload["type"] == "access"

    def test_verify_refresh_token(self) -> None:
        """测试验证刷新令牌."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_refresh_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_verify_invalid_token(self) -> None:
        """测试验证无效令牌."""
        payload = verify_token("invalid.token.here")

        assert payload is None

    def test_access_token_has_expiration(self) -> None:
        """测试访问令牌有过期时间."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert "exp" in payload
