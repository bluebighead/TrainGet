#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录模块
"""

import os
import logging
from logging.handlers import RotatingFileHandler


class UTF8StreamHandler(logging.StreamHandler):
    """
    处理控制台输出的编码问题
    """
    def emit(self, record):
        try:
            # 尝试使用UTF-8编码
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            # 如果失败，使用替代方法
            try:
                # 尝试将消息转换为UTF-8，忽略无法编码的字符
                msg = self.format(record)
                if isinstance(msg, str):
                    msg = msg.encode('utf-8', 'ignore').decode('utf-8')
                stream = self.stream
                stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                # 如果仍然失败，使用最基本的方法
                super().emit(record)


def setup_logger(name="train_get", log_file="train_get.log", level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
    
    Returns:
        logger: 日志记录器实例
    """
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    
    # 清除已存在的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # 使用UTF-8编码写入文件
    )
    file_handler.setLevel(level)
    
    # 创建控制台处理器（使用自定义的UTF8StreamHandler）
    console_handler = UTF8StreamHandler()
    console_handler.setLevel(level)
    
    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 创建默认日志记录器
logger = setup_logger()
