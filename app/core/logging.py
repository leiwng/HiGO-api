# /app/core/logging.py
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

def setup_logging():
    """配置 Loguru 日志记录器"""
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=False,
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    logger.info("Logger configured successfully.")

def get_logger(name: str | None = None):  # 修复类型注解
    """获取日志记录器实例"""
    if name:
        return logger.bind(name=name)
    return logger

__all__ = ["setup_logging", "get_logger", "logger"]
