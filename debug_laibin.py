#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试来宾站点编码和反爬问题
"""

import sys
import os
import json
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def debug_query(start_station, end_station, query_date):
    """
    调试查询问题
    """
    logger.info(f"开始调试查询: {start_station} -> {end_station}, 日期: {query_date}")
    
    try:
        # 创建会话
        session = requests.Session()
        
        # 1. 访问首页，获取cookie和会话信息
        logger.info("1. 访问12306首页获取会话信息...")
        index_url = "https://kyfw.12306.cn/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        index_response = session.get(index_url, headers=headers)
        logger.info(f"首页访问成功，状态码: {index_response.status_code}")
        
        # 2. 访问余票查询页面，获取更多cookie
        logger.info("2. 访问余票查询页面...")
        left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
        left_ticket_response = session.get(left_ticket_url, headers=headers)
        logger.info(f"余票查询页面访问成功，状态码: {left_ticket_response.status_code}")
        
        # 3. 获取站点编码
        logger.info("3. 获取站点编码...")
        station_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        station_response = session.get(station_url, headers=headers)
        logger.info(f"站点编码获取成功，状态码: {station_response.status_code}")
        
        # 解析站点编码
        station_text = station_response.text
        station_dict = {}
        import re
        station_list = re.findall(r'([\\u4e00-\\u9fa5]+)\\|([A-Z]+)', station_text)
        for station_name, station_code in station_list:
            station_dict[station_name] = station_code
        
        logger.info(f"解析到 {len(station_dict)} 个站点")
        
        # 检查站点编码
        if start_station in station_dict:
            from_station = station_dict[start_station]
            logger.info(f"{start_station} 的编码: {from_station}")
        else:
            logger.error(f"未找到站点: {start_station}")
            return
        
        if end_station in station_dict:
            to_station = station_dict[end_station]
            logger.info(f"{end_station} 的编码: {to_station}")
        else:
            logger.error(f"未找到站点: {end_station}")
            return
        
        # 4. 发送查询请求
        logger.info("4. 发送查询请求...")
        query_url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": query_date,
            "leftTicketDTO.from_station": from_station,
            "leftTicketDTO.to_station": to_station,
            "purpose_codes": "ADULT"
        }
        
        query_headers = headers.copy()
        query_headers.update({
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        
        query_response = session.get(query_url, params=params, headers=query_headers)
        logger.info(f"查询请求成功，状态码: {query_response.status_code}")
        
        # 保存响应内容到文件
        debug_file = f"debug_{start_station}_{end_station}_{query_date}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(query_response.text)
        logger.info(f"响应内容已保存到 {debug_file}")
        
        # 5. 尝试解析响应内容
        logger.info("5. 解析响应内容...")
        try:
            result = query_response.json()
            logger.info(f"JSON解析成功")
            logger.info(f"响应状态: {result.get('status')}")
            logger.info(f"响应消息: {result.get('messages')}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容前1000字符: {query_response.text[:1000]}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    # 测试北海到来宾的查询
    debug_query("北海", "来宾", "2026-02-21")
