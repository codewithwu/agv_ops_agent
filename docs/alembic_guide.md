# Alembic 数据库迁移指南

## 概述

Alembic 是 SQLAlchemy 的数据库迁移管理工具，支持版本化、自动生成迁移脚本、回滚等功能。

---

## 常用命令

### 初始化

```bash
# 初始化迁移目录
alembic init alembic
```

### 生成迁移

```bash
# 自动生成迁移脚本 (根据模型变更)
alembic revision --autogenerate -m "描述信息"

# 手动创建空白迁移脚本
alembic revision -m "描述信息"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision>

# 升级一步
alembic upgrade +1
```

### 回滚

```bash
# 回滚一步
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>

# 回滚所有迁移
alembic downgrade base
```

### 查看状态

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看详细信息
alembic history --verbose

# 查看待执行迁移
alembic check
```

### 其他

```bash
# 显示迁移脚本路径
alembic heads

# 合并多个迁移
alembic merge <revision1> <revision2> -m "merge"
```

---

## 配置文件

### alembic.ini

主配置文件，主要配置项：

```ini
[alembic]
# 迁移脚本目录
script_location = alembic

# 迁移文件命名模板 (默认)
file_template = %%(rev)s_%%(slug)s

# 带时间戳格式 (推荐)
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s

# 数据库连接 URL (可在 env.py 中覆盖)
sqlalchemy.url = postgresql://user:pass@localhost:5432/dbname
```

**命名模板变量**:
| 变量 | 说明 |
|------|------|
| `%(year)d` | 年 (4位) |
| `%(month).2d` | 月 (2位) |
| `%(day).2d` | 日 (2位) |
| `%(hour).2d` | 时 (2位) |
| `%(minute).2d` | 分 (2位) |
| `%(second).2d` | 秒 (2位) |
| `%(rev)s` |  revision ID |
| `%(slug)s` |  描述信息 (slug 格式) |

### env.py

迁移环境配置，核心功能：

```python
from src.database import Base
from src.models import *  # 导入所有模型

target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

## 迁移脚本结构

```python
"""描述信息

Revision ID: fc70045eac6e
Revises:
Create Date: 2026-04-16 08:38:45.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'fc70045eac6e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级操作."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        # ...
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """降级操作."""
    op.drop_table('users')
```

---

## 常用操作示例

### 创建表

```python
def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), unique=True),
    )
```

### 删除表

```python
def downgrade() -> None:
    op.drop_table('user')
```

### 添加列

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
```

### 删除列

```python
def downgrade() -> None:
    op.drop_column('users', 'age')
```

### 添加索引

```python
def upgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'])
```

### 重命名表

```python
def upgrade() -> None:
    op.rename_table('user', 'users')
```

### 修改列类型

```python
def upgrade() -> None:
    op.alter_column('users', 'name', type_=sa.String(100))
```

---

## 工作流程

1. **修改模型** - 在 `src/models/` 中修改 SQLAlchemy 模型
2. **生成迁移** - `alembic revision --autogenerate -m "描述"`
3. **检查脚本** - 查看生成的 `alembic/versions/` 文件
4. **应用迁移** - `alembic upgrade head`
5. **如需回滚** - `alembic downgrade -1`

---

## 注意事项

- `down_revision` 必须指向上一个迁移版本
- 手动编辑迁移时注意保持 `upgrade`/`downgrade` 对称
- 生产环境回滚前务必备份数据
- 使用 `--autogenerate` 前确保模型已正确导入
