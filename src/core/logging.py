#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
留学助手日志配置模块

使用 colorlog 提供丰富的彩色日志输出，支持多种日志格式和输出方式。
包含开发环境彩色输出和生产环境结构化日志。

主要特性：
- 彩色控制台输出（开发环境）
- JSON 结构化日志（生产环境）
- 文件日志记录
- 日志级别动态切换
- 支持中文日志消息
- 异常堆栈跟踪
- 上下文信息记录
"""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 尝试导入 colorlog，如果没有安装则使用标准日志
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False
    print("警告: colorlog 未安装，将使用标准日志格式。运行 'pip install colorlog' 安装。")

from logging import Formatter, LogRecord


class EnhancedJsonFormatter(Formatter):
    """
    增强的 JSON 格式化器
    
    为生产环境提供结构化的 JSON 日志输出，包含丰富的上下文信息。
    """
    
    def format(self, record: LogRecord) -> str:
        """格式化日志记录为 JSON 字符串"""
        # 构建基础日志记录
        log_record: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # 添加额外信息
        if hasattr(record, 'extra_info'):
            log_record["extra_info"] = record.extra_info
        
        # 添加用户和租户信息
        for attr in ['user_id', 'tenant_id', 'request_id', 'ip_address']:
            if hasattr(record, attr):
                log_record[attr] = getattr(record, attr)
        
        return json.dumps(log_record, ensure_ascii=False, indent=None)


class ColoredConsoleFormatter(Formatter):
    """
    彩色控制台格式化器
    
    当 colorlog 不可用时使用的备用彩色格式化器。
    """
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m',       # 重置
        'BLUE': '\033[34m',       # 蓝色
        'BOLD': '\033[1m',        # 粗体
    }
    
    def format(self, record: LogRecord) -> str:
        """格式化日志记录并添加颜色"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        blue = self.COLORS['BLUE']
        bold = self.COLORS['BOLD']
        
        # 格式化时间
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # 构建彩色消息
        message = f"{color}{bold}[{record.levelname:5}]{reset} {blue}{timestamp}{reset} {blue}{record.name}{reset}: {record.getMessage()}"
        
        return message


def get_logging_config(use_colors: bool = True, log_level: str = "INFO", log_to_file: bool = True) -> Dict[str, Any]:
    """
    获取日志配置
    
    Args:
        use_colors (bool): 是否使用彩色输出
        log_level (str): 日志级别
        log_to_file (bool): 是否记录到文件
        
    Returns:
        Dict[str, Any]: 日志配置字典
    """
    
    # 确保日志目录存在
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    # 选择格式化器
    if use_colors and COLORLOG_AVAILABLE:
        console_formatter = "colorlog"
    elif use_colors:
        console_formatter = "colored_console"
    else:
        console_formatter = "simple"
    
    # 构建格式化器配置
    formatters = {
        # 备用彩色格式化器
        "colored_console": {
            "()": ColoredConsoleFormatter,
        },
        # 简单格式化器
        "simple": {
            "format": "[%(levelname)-5s] %(asctime)s %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
        # JSON 格式化器
        "json": {
            "()": EnhancedJsonFormatter,
        },
    }
    
    # 如果 colorlog 可用，添加 colorlog 格式化器
    if use_colors and COLORLOG_AVAILABLE:
        formatters["colorlog"] = {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(bold)s[%(levelname)-5s]%(reset)s %(blue)s%(asctime)s%(reset)s %(cyan)s%(name)s%(reset)s: %(log_color)s%(message)s%(reset)s",
            "datefmt": "%H:%M:%S",
            "log_colors": {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            "secondary_log_colors": {},
            "style": '%'
        }
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": console_formatter,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {  # 根日志器
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "src": {  # 应用日志
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            }
        },
    }
    
    # 添加文件日志处理器
    if log_to_file:
        config["handlers"]["file"] = {
            "level": log_level,
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "json",
            "encoding": "utf-8",
        }
        config["handlers"]["error_file"] = {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "logs/error.log",
            "formatter": "json",
            "encoding": "utf-8",
        }
        
        # 将文件处理器添加到日志器
        for logger_name in config["loggers"]:
            if logger_name == "":
                config["loggers"][logger_name]["handlers"] = ["console", "file"]
            else:
                config["loggers"][logger_name]["handlers"] = ["console", "file", "error_file"]
    
    return config


def setup_logging(
    log_level: str = "INFO",
    use_colors: bool = True,
    log_to_file: bool = True,
    environment: str = "development"
):
    """
    设置应用程序日志配置
    
    优先使用环境变量，如果没有设置则使用默认值：
    - DEBUG: 控制是否启用调试模式（影响日志级别和彩色输出）
    - LOG_LEVEL: 设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - ENV: 设置环境类型 (development, test, production)
    
    Args:
        log_level (str, optional): 日志级别，如果为None则从环境变量获取
        use_colors (bool, optional): 是否使用彩色输出，如果为None则根据环境变量自动判断
        log_to_file (bool, optional): 是否记录到文件，如果为None则根据环境变量自动判断
        environment (str, optional): 环境类型，如果为None则从环境变量获取
    """
    # 从环境变量获取配置
    debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    env_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    env_environment = os.getenv("ENV", "development")
    
    # 使用参数或环境变量
    final_log_level = log_level or env_log_level
    final_environment = environment or env_environment
    
    # 根据DEBUG环境变量自动设置日志级别
    if debug_mode and log_level is None:
        final_log_level = "DEBUG"
    
    # 根据环境变量自动设置彩色输出
    if use_colors is None:
        if debug_mode:
            use_colors = True
        elif final_environment == "production":
            use_colors = False
        else:
            use_colors = True
    
    # 根据环境变量自动设置文件日志
    if log_to_file is None:
        if final_environment in ("production", "test"):
            log_to_file = True
        else:
            log_to_file = debug_mode
    
    # 验证日志级别
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if final_log_level not in valid_levels:
        print(f"警告: 无效的日志级别 '{final_log_level}'，使用默认级别 'INFO'")
        final_log_level = "INFO"
    
    config = get_logging_config(use_colors, final_log_level, log_to_file)
    logging.config.dictConfig(config)
    
    # 输出配置信息
    logger = logging.getLogger(__name__)
    logger.info(
        f"日志系统已初始化 - "
        f"级别: {final_log_level}, "
        f"彩色: {use_colors}, "
        f"文件: {log_to_file}, "
        f"环境: {final_environment}, "
        f"调试模式: {debug_mode}"
    )


def get_logger(name: str, extra_info: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    获取配置好的日志器实例
    
    Args:
        name (str): 日志器名称，通常使用 __name__
        extra_info (Dict[str, Any], optional): 额外的上下文信息
        
    Returns:
        logging.Logger: 配置好的日志器实例
    """
    logger = logging.getLogger(name)
    
    # 如果有额外信息，创建一个适配器
    if extra_info:
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                kwargs['extra'] = {'extra_info': extra_info}
                return msg, kwargs
        
        logger = ContextAdapter(logger, extra_info)
    
    return logger


# 便捷的日志记录函数
def log_user_action(logger: logging.Logger, user_id: int, action: str, 
                   tenant_id: Optional[int] = None, **kwargs):
    """记录用户操作的便捷函数"""
    extra = {
        'user_id': user_id,
        'action': action,
        **kwargs
    }
    
    if tenant_id:
        extra['tenant_id'] = tenant_id
    
    logger.info(f"用户 {user_id} 执行操作: {action}", extra={'extra_info': extra})


def log_api_request(logger: logging.Logger, method: str, path: str, 
                   status_code: int, user_id: Optional[int] = None, 
                   tenant_id: Optional[int] = None, **kwargs):
    """记录 API 请求的便捷函数"""
    extra = {
        'method': method,
        'path': path,
        'status_code': status_code,
        **kwargs
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    if tenant_id:
        extra['tenant_id'] = tenant_id
    
    level = 'INFO' if status_code < 400 else 'WARNING' if status_code < 500 else 'ERROR'
    
    getattr(logger, level.lower())(
        f"API 请求: {method} {path} - 状态码: {status_code}",
        extra={'extra_info': extra}
    )


def get_default_logging_config():
    """
    获取基于环境变量的默认日志配置
    
    这个函数不会自动应用配置，需要手动调用 setup_logging() 来应用配置。
    """
    # 从环境变量获取配置
    debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENV", "development")
    
    # 根据DEBUG环境变量自动设置日志级别
    if debug_mode:
        log_level = "DEBUG"
    
    # 根据环境变量自动设置彩色输出
    if debug_mode:
        use_colors = True
    elif environment == "production":
        use_colors = False
    else:
        use_colors = COLORLOG_AVAILABLE
    
    # 根据环境变量自动设置文件日志
    if environment in ("production", "test"):
        log_to_file = True
    else:
        log_to_file = debug_mode
    
    return get_logging_config(use_colors, log_level, log_to_file)


def init_logging_from_env():
    """
    根据环境变量快速初始化日志系统
    
    这是一个便捷函数，会根据当前的环境变量自动配置日志系统。
    推荐在应用程序启动时调用此函数。
    """
    setup_logging()


# 默认的日志配置（基于环境变量）
LOGGING_CONFIG = get_default_logging_config()

# 注意：不要在模块导入时自动调用 setup_logging
# 这会导致重复初始化日志系统
# 应该在应用程序启动时手动调用 setup_logging() 或 init_logging_from_env()
