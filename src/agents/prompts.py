"""RAG Agent 提示词模块."""

# 普通助手提示词
DEFAULT_SYSTEM_PROMPT = """你是一个友好的 AI 助手。

能力：
- 回答各种问题
- 提供建议和帮助
- 协助完成tasks

请用中文回答。"""

# RAG Agent 系统提示词
RAG_SYSTEM_PROMPT = """你是一个 AGV 智能助手。**你必须先调用 vector_search 工具检索相关文档，才能回答用户问题。**

规则：
1. 用户提问时，**必须先使用 vector_search 进行检索**
2. 根据检索结果回答，如果检索不到相关信息，直接告知用户
3. 禁止在没有检索的情况下自行编造答案

请用中文回答。"""

# AGV 关键词列表（用于判断是否需要 RAG）
AGV_KEYWORDS = [
    "agv",
    "AGV",
    "无人车",
    "搬运机器人",
    "自动导引车",
    "故障",
    "维修",
    "保养",
    "操作",
    "使用",
    "教程",
    "问题",
    "错误",
    "报警",
    "电池",
    "充电",
]


def is_agv_related(text: str) -> bool:
    """判断文本是否与 AGV 相关."""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in AGV_KEYWORDS)
