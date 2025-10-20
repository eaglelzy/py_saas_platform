#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置使用示例

展示如何使用环境变量来控制日志配置
"""

import os
from src.core.logging import setup_logging, init_logging_from_env, get_logger

def example_usage():
    """展示日志配置的使用方法"""
    
    print("=== 日志配置使用示例 ===\n")
    
    # 方法1: 手动设置环境变量后初始化
    print("1. 手动设置环境变量后初始化:")
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENV"] = "test"
    
    init_logging_from_env()
    
    logger = get_logger(__name__)
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息")
    logger.warning("这是一条警告")
    logger.error("这是一条错误")
    
    print("\n" + "="*50 + "\n")
    
    # 方法2: 直接调用setup_logging并传入参数
    print("2. 直接调用setup_logging并传入参数:")
    setup_logging(
        log_level="INFO",
        use_colors=True,
        log_to_file=False,
        environment="development"
    )
    
    logger2 = get_logger(__name__)
    logger2.info("使用手动参数配置的日志")
    
    print("\n" + "="*50 + "\n")
    
    # 方法3: 生产环境配置
    print("3. 生产环境配置:")
    os.environ["DEBUG"] = "false"
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["ENV"] = "production"
    
    init_logging_from_env()
    
    logger3 = get_logger(__name__)
    logger3.debug("这条调试信息不会显示（生产环境）")
    logger3.info("这条信息不会显示（生产环境）")
    logger3.warning("这条警告会显示")
    logger3.error("这条错误会显示")

if __name__ == "__main__":
    example_usage()
