#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找桂林的正确站点编码
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def find_guilin_code():
    """
    查找桂林的正确站点编码
    """
    logger.info("开始查找桂林的站点编码")
    
    try:
        # 获取站点编码文件
        station_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        
        response = requests.get(station_url, headers=headers)
        logger.info(f"站点编码获取成功，状态码: {response.status_code}")
        
        # 查找包含桂林的站点
        content = response.text
        logger.info("查找包含桂林的站点...")
        
        # 按@分割
        stations = content.split('@')
        for station in stations:
            if "桂林" in station:
                logger.info(f"找到桂林站点: {station}")
        
    except Exception as e:
        logger.error(f"查找失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    find_guilin_code()
