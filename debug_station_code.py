#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试站点编码解析问题
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def debug_station_code():
    """
    调试站点编码解析
    """
    logger.info("开始调试站点编码解析")
    
    try:
        # 获取站点编码文件
        station_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        
        response = requests.get(station_url, headers=headers)
        logger.info(f"站点编码获取成功，状态码: {response.status_code}")
        
        # 保存原始内容到文件
        with open("station_name.js", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("站点编码文件已保存到 station_name.js")
        
        # 打印前1000字符，查看文件结构
        logger.info("站点编码文件前1000字符:")
        logger.info(response.text[:1000])
        
        # 尝试不同的解析方式
        logger.info("\n尝试解析站点编码...")
        import re
        
        # 方式1: 直接查找中文和大写字母的组合
        pattern1 = r'([\u4e00-\u9fa5]+)\|([A-Z]+)'
        matches1 = re.findall(pattern1, response.text)
        logger.info(f"方式1 解析到 {len(matches1)} 个站点")
        if matches1:
            logger.info(f"前10个站点: {matches1[:10]}")
        
        # 方式2: 先提取station_names变量内容，再解析
        pattern2 = r'var station_names = "([^"]+)"'
        match2 = re.search(pattern2, response.text)
        if match2:
            station_data = match2.group(1)
            logger.info(f"方式2 提取到站点数据长度: {len(station_data)}")
            stations = station_data.split('|')
            logger.info(f"方式2 分割后得到 {len(stations)} 个元素")
            # 每5个元素一组
            for i in range(0, len(stations), 5):
                if i + 1 < len(stations):
                    station_name = stations[i]
                    station_code = stations[i+1]
                    logger.info(f"站点: {station_name}, 编码: {station_code}")
                    if station_name == "北海":
                        logger.info(f"找到北海站点，编码: {station_code}")
                    if station_name == "来宾":
                        logger.info(f"找到来宾站点，编码: {station_code}")
                if i > 100:  # 只打印前20个站点
                    break
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_station_code()
