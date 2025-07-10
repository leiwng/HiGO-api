# /app/core/logging.py
import sys
from loguru import logger
from .config import settings

def setup_logging():
    """
    Configures the Loguru logger for the application.
    """
    logger.remove()  # Remove default handler

    # Console logger
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File logger
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",  # Rotates the log file when it reaches 10 MB
        retention="7 days",  # Keeps logs for 7 days
        compression="zip",  # Compresses old log files
        serialize=False,  # Set to True to output JSON logs
        enqueue=True, # Make logging async-safe
        backtrace=True,
        diagnose=True
    )

    logger.info("Logger configured successfully.")
