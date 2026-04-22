# AGV Ops Agent

AGV（自动导引车）智能运维助手，基于 RAG（检索增强生成）技术，为 AGV 运维提供智能问答服务。

## 功能特性

- **用户认证**：JWT 认证，支持注册、登录、登出、令牌刷新
- **文档管理**：上传 PDF、Markdown、TXT 文档，自动向量化存储
- **RAG 智能问答**：基于文档内容进行 AI 智能问答
- **向量检索**：支持 PGVector 向量数据库存储与检索
- **前端界面**：React + TypeScript + TailwindCSS 构建的现代化界面

## 技术栈

**后端**
- Python 3.12+
- FastAPI - Web 框架
- SQLAlchemy (async) - 异步 ORM
- PostgreSQL + PGVector - 关系数据库 + 向量存储
- LangChain - LLM 应用框架
- python-jose - JWT 认证

**前端**
- React 18 + TypeScript
- Vite - 构建工具
- TailwindCSS - 样式框架
- Axios - HTTP 客户端

## 项目结构

```
project-root/
├── src/                    # 后端源码
│   ├── main.py             # FastAPI 应用入口
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接
│   ├── api/                # API 路由
│   │   └── v1/
│   │       ├── auth.py     # 认证接口
│   │       ├── user.py     # 用户接口
│   │       ├── file.py     # 文件接口
│   │       └── agent.py    # AI Agent 接口
│   ├── models/             # Pydantic 数据模型
│   ├── services/           # 业务逻辑
│   ├── agents/            # RAG Agent
│   ├── tasks/             # 异步任务
│   └── utils/             # 工具函数
├── frontend/               # 前端源码
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   └── App.tsx
│   └── package.json
├── alembic/                # 数据库迁移
├── tests/                  # 测试代码
└── docs/                   # 文档
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ (需启用 pgvector 扩展)
- uv (Python 包管理器)

### 2. 后端安装

```bash
# 克隆项目
cd agv_ops_agent

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库连接等配置

# 执行数据库迁移
uv run alembic upgrade head

# 启动服务
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端默认运行在 http://localhost:5173，会代理 API 请求到后端 http://localhost:8000。

### 4. 环境变量配置

`.env` 文件主要配置项：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agv_ops
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/agv_ops
PGVECTOR_CONNECTION=postgresql://user:pass@localhost:5432/agv_ops

# JWT 认证
JWT_SECRET_KEY=your-secret-key

# 向量化模型 (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL_NAME=qwen3-embedding:8b

# LLM 模型 (OpenAI/LongCat)
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.longcat.chat/openai
OPENAI_MODEL_NAME=LongCat-Flash-Chat
```

## API 接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | 否 |
| POST | `/api/v1/auth/login` | 用户登录 | 否 |
| POST | `/api/v1/auth/logout` | 退出登录 | 是 |
| POST | `/api/v1/auth/refresh` | 刷新令牌 | 否 |
| GET | `/api/v1/auth/me` | 获取当前用户 | 是 |
| GET | `/api/v1/users` | 获取所有用户 | 是 |
| POST | `/api/v1/files/upload` | 上传文档 | 是 |
| GET | `/api/v1/files` | 获取文件列表 | 是 |
| POST | `/api/v1/agent/chat` | RAG 智能问答 | 是 |
| GET | `/api/v1/health` | 健康检查 | 否 |

## 开发指南

```bash
# 代码格式化
uv run ruff format . && uv run ruff check --fix .

# 类型检查
uv run mypy src/

# 运行测试
uv run pytest -v
```

## 相关文档

- [AGV 基本操作手册](./01_AGV基本操作手册.md)
- [常见问题](./questions.md)
- [Alembic 迁移指南](./docs/alembic_guide.md)
- [开发规范](./CLAUDE.md)

## License

MIT
