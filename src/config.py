"""应用配置模块."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量加载的应用配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AGV Ops Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    # 日志配置
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # 应用根目录（用于日志等文件路径）
    app_root: Path = Path(__file__).parent.parent

    cors_origins: list[str] = ["*"]

    # 数据库连接
    database_url: str = ""
    database_url_sync: str = ""

    # PGVector 向量存储连接（psycopg 同步驱动）
    pgvector_connection: str = ""

    # JWT 配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ===== Embedding 配置 =====

    # Ollama 配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model_name: str = "qwen3-embedding:8b"

    # OpenAI/ModelScope 配置
    openai_embedding_api_key: str = ""
    openai_embedding_base_url: str = "https://api-inference.modelscope.cn/v1"
    openai_embedding_model_name: str = "Qwen/Qwen3-Embedding-8B"

    # 支持向量化的文件扩展名
    vectorizable_extensions: set[str] = {".pdf", ".md", ".txt"}

    # ===== LLM 配置 =====

    # Ollama LLM 配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "qwen3.5:9b"

    # OpenAI LLM 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.longcat.chat/openai"
    openai_model_name: str = "LongCat-Flash-Chat"

    # Ling LLM 配置（备用模型）
    ling_api_key: str = ""
    ling_baseurl: str = ""
    ling_model_name: str = ""


settings = Settings()
