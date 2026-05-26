import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """
    设置并返回一个 logger 实例

    Args:
        name: logger 名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式字符串（可选）
        date_format: 日期格式字符串（可选）

    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 默认日志格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

    # 默认日期格式
    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # 创建格式化器
    formatter = logging.Formatter(format_string, date_format)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建全局 logger 实例
logger = setup_logger(name="rag_project", level=logging.INFO, log_file="logs/rag.log")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，如果为 None 则返回全局 logger

    Returns:
        Logger 实例
    """
    if name:
        return setup_logger(name)
    return logger
