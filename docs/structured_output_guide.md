# LangGraph 结构化输出指南

## 1. 基本结构化输出

使用 `response_format=ToolStrategy(Schema)` 为 agent 添加结构化输出能力。

```python
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

agent = create_agent(
    model="gpt-5.4-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "提取联系人: John Doe, john@example.com, (555) 123-4567"}]
})

# 获取结构化结果
structured_output = result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

## 2. 多类型结构化输出（Union）

使用 `Union` 让模型在多个结构中选择返回其中一个。

```python
from typing import Union
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

# 定义多种结构
class ContactInfo(BaseModel):
    name: str
    email: str

class Product(BaseModel):
    product_id: str
    price: float

# Union 支持返回其中一种类型
Response = Union[ContactInfo, Product]

agent = create_agent(
    model="gpt-5.4-mini",
    tools=[],
    response_format=ToolStrategy(Response)
)

# 场景1：提取联系人
result1 = agent.invoke({
    "messages": [{"role": "user", "content": "提取联系人：张三, zhangsan@example.com"}]
})
# ContactInfo(name='张三', email='zhangsan@example.com')

# 场景2：提取产品
result2 = agent.invoke({
    "messages": [{"role": "user", "content": "提取产品：商品编号 P123，价格 99.9 元"}]
})
# Product(product_id='P123', price=99.9)
```

### 模型如何选择类型？

根据用户输入的内容自动判断返回哪种类型：

| 输入内容 | 判断类型 |
|----------|----------|
| "张三, zhangsan@example.com" | `ContactInfo` |
| "商品编号 P123，价格 99.9 元" | `Product` |

## 3. 同时返回多个结构（父类包装）

如果需要同时返回多种类型，用父类包装。

```python
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str
    email: str

class Product(BaseModel):
    product_id: str
    price: float

# 父类包装多种类型
class ExtractedData(BaseModel):
    contact: ContactInfo | None = None
    product: Product | None = None
    notes: str = ""

agent = create_agent(
    model="gpt-5.4-mini",
    tools=[],
    response_format=ToolStrategy(ExtractedData)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "提取：联系人张三 zhangsan@example.com，产品 P123 价格 99.9 元"}]
})
# ExtractedData(
#     contact=ContactInfo(name='张三', email='zhangsan@example.com'),
#     product=Product(product_id='P123', price=99.9),
#     notes=''
# )
```

## 4. 流式结构化输出

流式输出时，结构化结果会在最后一个 chunk 返回。

```python
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "提取联系人: John Doe, john@example.com"}]},
    stream_mode="messages",
    config={"configurable": {"thread_id": "1"}},
):
    # 检查是否是 ContactInfo 类型的 tool 返回
    if hasattr(token, 'name') and token.name == 'ContactInfo':
        # 这就是结构化结果
        structured_result = token.content
        print(f"结构化结果: {structured_result}")
```

### 流式输出的 token 结构

| 阶段 | token 内容 |
|------|------------|
| 中间 | `invalid_tool_calls` 逐字累积 JSON 片段 |
| 最后 | 完整的 `ContactInfo` 对象 |

## 5. 常见使用场景

| 场景 | 示例结构 |
|------|----------|
| 数据提取 | `ContactInfo`, `Address`, `Invoice` |
| AGV 故障报告 | `FaultReport`, `FaultCode` |
| AGV 状态查询 | `AGVStatus`, `BatteryInfo` |
| 定时任务配置 | `ScheduleTask`, `CronExpression` |
| 表单填充 | `FormData`, `UserProfile` |

## 6. AGV 项目中的示例

### 故障报告提取

```python
class FaultReport(BaseModel):
    fault_code: str           # 故障代码
    fault_level: str          # 严重程度：critical/warning/info
    description: str          # 故障描述
    suggestion: str            # 建议操作

response_format=ToolStrategy(FaultReport)
```

### AGV 状态查询

```python
class AGVStatus(BaseModel):
    agv_id: str
    battery_level: int        # 0-100
    current_position: str
    task_status: str          # idle/running/charging/error
    last_update: str

response_format=ToolStrategy(AGVStatus)
```

## 7. 注意事项

1. **`Union` 是二选一**：模型根据内容自动选择一个类型返回
2. **不是同时返回多个**：如需同时返回多个，用父类包装
3. **流式需要累积**：流式模式下最后一个 chunk 才包含完整结构
4. **Schema 需要完整**：所有字段都要有类型定义

## 8. 参考链接

- [LangChain Structured Output](https://python.langchain.com/docs/concepts/structured_output/)
- [Pydantic BaseModel](https://docs.pydantic.dev/)
