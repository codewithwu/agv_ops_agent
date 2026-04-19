"""文件相关的后台任务."""

import logging
import os
from pathlib import Path

from src.services.vectorstore import get_vectorstore_service

logger = logging.getLogger(__name__)


def vectorize_file(file_path: str, metadata: dict) -> None:
    """向量化和存储文件（后台任务）.

    Args:
        file_path: 文件路径
        metadata: 元数据，包含 user_id, file_id 等
    """
    try:
        service = get_vectorstore_service()
        service.add_documents(file_path, metadata)
        logger.info(f"文件向量化成功: {file_path}")
    except Exception as e:
        logger.error(f"文件向量化失败: {file_path}, 错误: {e}")


def delete_vectorstore_entries(file_path: str) -> None:
    """删除向量存储中的相关条目（后台任务）.

    Args:
        file_path: 文件路径
    """
    try:
        # TODO: 根据 file_path 删除向量存储中的文档
        pass
    except Exception as e:
        logger.error(f"删除向量存储失败: {file_path}, 错误: {e}")


def cleanup_physical_file(file_path: str) -> None:
    """清理物理文件（后台任务）.

    Args:
        file_path: 物理文件路径
    """
    path = Path(file_path)
    if path.exists():
        os.remove(path)
