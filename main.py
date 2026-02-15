#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车票信息自动获取应用入口文件
"""

import sys
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()


def main():
    """应用主函数"""
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主窗口
        main_window = MainWindow()
        main_window.show()
        
        # 运行应用
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


if __name__ == "__main__":
    main()
