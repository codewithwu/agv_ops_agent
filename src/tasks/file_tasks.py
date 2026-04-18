"""文件相关的后台任务."""

import os
from pathlib import Path


def cleanup_physical_file(file_path: str) -> None:
    """清理物理文件（后台任务）.

    Args:
        file_path: 物理文件路径
    """
    path = Path(file_path)
    if path.exists():
        os.remove(path)
