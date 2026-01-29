"""
日志工具

配置统一格式的日志记录器
"""

import sys
import logging


def setup_logger(name: str = "gateway", level: str = "INFO") -> logging.Logger:
    """配置统一格式的日志

    Args:
        name: 日志记录器名称
        level: 日志级别（INFO, DEBUG, WARNING, ERROR）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 文本格式（输出到 stdout，Docker 自动收集）
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
