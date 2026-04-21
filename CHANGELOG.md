# 更新日志

## [Unreleased]

### 更新
- 优化 CLAUDE.md：允许 AI 执行安全的 Git 操作
- AI Agent 接口和逻辑优化
- 首页界面样式调整
- 相关测试更新

## [1.0.0] - 2026-04-16

### 项目初始化

#### 新增
- 初始化 FastAPI 项目框架
- 配置 `uv` 包管理器
- 配置 `ruff` 代码格式化工具
- 配置 `pytest` 测试框架

#### 项目结构
```
src/
├── __init__.py
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── database.py          # 异步数据库连接
├── api/
│   ├── __init__.py
│   ├── router.py        # API 路由聚合
│   └── v1/
│       ├── __init__.py
│       ├── health.py    # 健康检查
│       ├── auth.py      # 认证接口
│       └── user.py      # 用户接口
├── models/
│   ├── __init__.py
│   └── user.py          # User 数据模型
├── security/
│   ├── __init__.py
│   ├── jwt.py           # JWT 令牌工具
│   └── password.py      # 密码哈希工具
├── services/            # 业务逻辑层 (预留)
└── utils/               # 工具函数 (预留)
```

---

### 数据库集成

#### 新增
- 集成 PostgreSQL 数据库 (asyncpg 驱动)
- 配置 SQLAlchemy 异步 ORM
- 创建 `alembic` 数据库迁移工具
- `users` 数据表迁移脚本

#### User 表结构
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键自增 |
| username | String(50) | 用户名，唯一索引 |
| email | String(255) | 邮箱，唯一索引 |
| hashed_password | String(255) | 密码哈希 |
| is_active | Boolean | 激活状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### Alembic 配置
- 迁移文件命名格式: `YYYYMMDD_HHMMSS_<revision>_description.py`
- 使用 sync engine 进行迁移

---

### 认证功能

#### 新增
- **JWT 认证**: 集成 `python-jose` 实现 JWT 令牌
- **密码加密**: 使用 `bcrypt` 直接加密
- **Token 黑名单**: 内存存储黑名单 (生产环境应用 Redis)

#### API 接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | 否 |
| POST | `/api/v1/auth/login` | 用户登录 | 否 |
| POST | `/api/v1/auth/logout` | 退出登录 | 是 |
| POST | `/api/v1/auth/refresh` | 刷新令牌 | 否 |
| POST | `/api/v1/auth/change-password` | 修改密码 | 是 |
| GET | `/api/v1/auth/me` | 获取当前用户 | 是 |
| GET | `/api/v1/users` | 获取所有用户 | 是 |
| GET | `/api/v1/health` | 健康检查 | 否 |

#### JWT 配置
```python
jwt_secret_key: str = "your-secret-key-change-in-production"
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 30
jwt_refresh_token_expire_days: int = 7
```

#### 登录返回
```json
{
  "access_token": "xxx",
  "refresh_token": "yyy",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### 代码规范

#### 新增
- 所有代码注释使用中文
- Docstring 规范
- 函数命名规范 (snake_case)
- 类命名规范 (PascalCase)

#### 配置
- `alembic.ini`: 迁移文件时间戳命名
- `.env`: 环境变量配置

---

### 测试

#### 新增
- `tests/conftest.py`: pytest 配置，使用 SQLite 内存数据库
- `tests/test_auth.py`: 17 个认证接口测试
- `tests/test_user.py`: 3 个用户接口测试
- `tests/test_health.py`: 1 个健康检查测试
- `tests/test_security.py`: 9 个安全工具测试

#### 测试依赖
- `aiosqlite`: SQLite 异步驱动 (测试用)
- `httpx`: HTTP 客户端 (测试用)
- `pytest-asyncio`: 异步测试支持

#### 测试结果
```
30 passed, 22 warnings
```

---

### 文档

#### 新增
- `docs/alembic_guide.md`: Alembic 迁移指南
- `README.md`: 项目说明文档
- `CLAUDE.md`: 开发规范

---

### 删除

#### 删除
- ~~`src/api/v1/example.py`~~: 示例接口 (已移除)
- ~~`src/models/example.py`~~: 示例模型 (已移除)
- ~~`tests/test_example.py`~~: 示例测试 (已移除)

---

### 依赖列表

#### 生产依赖
```
fastapi
uvicorn
pydantic-settings
sqlalchemy
alembic
psycopg2-binary
asyncpg
python-jose
bcrypt
email-validator
```

#### 开发依赖
```
pytest
pytest-asyncio
ruff
httpx
aiosqlite
```
