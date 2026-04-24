"""日志管理模块.

提供统一的日志配置，支持：
- 控制台输出（带颜色）
- 文件保存（按日期分割）
- 灵活的日志级别配置
"""

import logging
import sys
from pathlib import Path
from typing import Literal

from src.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色格式化器，用于控制台输出."""

    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LoggerManager:
    """日志管理器类.

    提供单例模式的日志记录器，支持：
    - 控制台输出（带颜色）
    - 文件保存到 logs 目录（可选）
    - 错误日志单独保存（可选）

    Attributes:
        _instance: 单例实例
        _loggers: 日志记录器缓存
    """

    _instance: "LoggerManager | None" = None
    _loggers: dict[str, logging.Logger] = {}

    def __new__(cls) -> "LoggerManager":
        """单例模式获取实例."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_log_dir(self) -> Path:
        """获取日志目录."""
        log_dir = Path(settings.app_root) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _create_file_handler(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        filename: str,
    ) -> logging.FileHandler:
        """创建文件处理器.

        Args:
            level: 日志级别
            filename: 文件名

        Returns:
            FileHandler 实例
        """
        log_dir = self._get_log_dir()
        filepath = log_dir / filename

        handler = logging.FileHandler(filepath, encoding="utf-8")
        handler.setLevel(getattr(logging, level))
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        return handler

    def get_logger(
        self,
        name: str = "root",
        enable_file: bool = True,
    ) -> logging.Logger:
        """获取日志记录器.

        Args:
            name: 日志记录器名称（会拼接为 "agv_ops.{name}"）
            enable_file: 是否启用文件保存，默认 True

        Returns:
            Logger 实例
        """
        full_name = f"agv_ops.{name}" if name != "root" else "agv_ops"
        level = settings.log_level

        if full_name in self._loggers:
            return self._loggers[full_name]

        logger = logging.getLogger(full_name)
        logger.setLevel(getattr(logging, level))
        logger.propagate = False

        # 控制台处理器（始终启用）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level))
        console_handler.setFormatter(
            ColoredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

        # 文件处理器（可选）
        if enable_file:
            # 常规日志
            file_handler = self._create_file_handler("INFO", f"{settings.app_name}.log")
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)

            # 错误日志
            error_handler = self._create_file_handler(
                "ERROR", f"{settings.app_name}_error.log"
            )
            error_handler.setLevel(logging.ERROR)
            logger.addHandler(error_handler)

        self._loggers[full_name] = logger
        return logger


# 创建全局日志管理器实例
_logger_manager = LoggerManager()

# 默认日志记录器
logger = _logger_manager.get_logger()


def get_logger(name: str = "root", enable_file: bool = True) -> logging.Logger:
    """获取指定名称的日志记录器.

    Args:
        name: 日志记录器名称（会拼接为 "agv_ops.{name}"）
        enable_file: 是否启用文件保存，默认 True

    Returns:
        Logger 实例
    """
    return _logger_manager.get_logger(name, enable_file)


# 仅输出到终端的日志记录器
console_logger = _logger_manager.get_logger(name="console", enable_file=False)
