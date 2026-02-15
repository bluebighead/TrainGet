#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动查找北海和来宾的站点编码
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def find_station_code():
    """
    手动查找北海和来宾的站点编码
    """
    logger.info("开始查找北海和来宾的站点编码")
    
    try:
        # 获取站点编码文件
        station_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        
        response = requests.get(station_url, headers=headers)
        logger.info(f"站点编码获取成功，状态码: {response.status_code}")
        
        # 保存文件
        with open("station_name.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("站点编码文件已保存到 station_name.txt")
        
        # 手动查找北海和来宾
        content = response.text
        
        # 查找北海
        beihai_index = content.find("北海")
        if beihai_index != -1:
            # 提取周围的内容
            beihai_context = content[beihai_index-50:beihai_index+50]
            logger.info(f"北海附近的内容: {beihai_context}")
        else:
            logger.error("未找到北海")
        
        # 查找来宾
        laibin_index = content.find("来宾")
        if laibin_index != -1:
            # 提取周围的内容
            laibin_context = content[laibin_index-50:laibin_index+50]
            logger.info(f"来宾附近的内容: {laibin_context}")
        else:
            logger.error("未找到来宾")
        
        # 尝试另一种方式：按@分割
        logger.info("\n尝试按@分割查找站点...")
        stations = content.split('@')
        logger.info(f"按@分割后得到 {len(stations)} 个元素")
        
        # 查找包含北海和来宾的站点
        for station in stations:
            if "北海" in station:
                logger.info(f"找到北海站点: {station}")
            if "来宾" in station:
                logger.info(f"找到来宾站点: {station}")
        
    except Exception as e:
        logger.error(f"查找失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    find_station_code()
