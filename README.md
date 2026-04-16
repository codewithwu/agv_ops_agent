# AGV Ops Agent

AGV 智能运维助手 - 基于 FastAPI 的 Web 后端系统

## 技术栈

- **框架**: FastAPI
- **Python**: 3.12+
- **包管理**: uv
- **验证**: Pydantic v2
- **测试**: pytest

## 项目结构

```
src/
├── __init__.py
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── api/                  # API 路由
│   ├── __init__.py
│   ├── router.py         # 路由聚合
│   └── v1/              # API v1 版本
│       ├── __init__.py
│       ├── health.py     # 健康检查
│       └── example.py    # 示例接口
├── models/              # Pydantic / Dataclass 模型
│   └── example.py
├── services/            # 业务逻辑层
└── utils/               # 工具函数
```

## 快速开始

```bash
# 安装依赖
uv sync

# 运行开发服务器
uv run uvicorn src.main:app --reload --port 8000

# 运行测试
uv run pytest -v

# 代码格式化
uv run ruff format . && uv run ruff check --fix .
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/examples` | 创建示例 |
| GET | `/api/v1/examples` | 列表示例 |
| GET | `/api/v1/examples/{id}` | 获取单个示例 |

## 扩展开发

新增 API 模块:

1. 在 `src/api/v1/` 创建新模块 (如 `tasks.py`)
2. 在 `src/api/router.py` 中注册路由
3. 使用依赖注入管理数据库连接等资源
