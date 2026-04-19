"""任务提交器模块.

统一的任务提交入口，目前使用 BackgroundTasks。
后续改为 Celery 时只需修改本模块。
"""

from src.tasks.file_tasks import vectorize_file


def submit_vectorize_task(file_path: str, metadata: dict, background_tasks) -> None:
    """提交向量化和存储任务（后台执行）.

    Args:
        file_path: 文件路径
        metadata: 元数据，包含 user_id, file_id 等
        background_tasks: FastAPI BackgroundTasks 实例
    """
    background_tasks.add_task(vectorize_file, file_path, metadata)
