#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试北海到杭州的查询问题
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

def debug_query():
    """
    调试北海到杭州的查询
    """
    logger.info("开始调试北海到杭州的查询")
    
    try:
        # 创建会话
        session = requests.Session()
        
        # 1. 访问首页
        logger.info("1. 访问12306首页...")
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
        
        # 2. 访问余票查询页面
        logger.info("2. 访问余票查询页面...")
        left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
        left_ticket_response = session.get(left_ticket_url, headers=headers)
        logger.info(f"余票查询页面访问成功，状态码: {left_ticket_response.status_code}")
        
        # 3. 发送查询请求
        logger.info("3. 发送查询请求...")
        query_url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": "2026-02-15",
            "leftTicketDTO.from_station": "BHZ",  # 北海
            "leftTicketDTO.to_station": "HZH",    # 杭州
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
        debug_file = "debug_beihai_hangzhou.json"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(query_response.text)
        logger.info(f"响应内容已保存到 {debug_file}")
        
        # 4. 解析响应内容
        logger.info("4. 解析响应内容...")
        try:
            result = query_response.json()
            logger.info(f"JSON解析成功")
            logger.info(f"响应状态: {result.get('status')}")
            logger.info(f"响应消息: {result.get('messages')}")
            
            # 处理查询结果
            if result.get("status"):
                data = result.get("data", {})
                result_list = data.get("result", [])
                logger.info(f"查询结果数量: {len(result_list)}")
                
                if result_list:
                    logger.info("查询成功，找到以下车次:")
                    for i, item in enumerate(result_list[:5]):  # 只显示前5条
                        fields = item.split("|")
                        if len(fields) > 3:
                            train_number = fields[3]
                            start_time = fields[8]
                            end_time = fields[9]
                            duration = fields[10]
                            logger.info(f"车次: {train_number}, 出发时间: {start_time}, 到达时间: {end_time}, 历时: {duration}")
                else:
                    logger.info("查询结果为空，可能没有直达车次")
                    # 检查是否有其他问题
                    logger.info(f"data: {data}")
            else:
                logger.error(f"查询失败，响应状态为False")
                logger.error(f"响应消息: {result.get('messages')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容前500字符: {query_response.text[:500]}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_query()
