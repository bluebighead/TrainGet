#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用高级反爬策略调试查询问题
"""

import sys
import os
import json
import requests
import time
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def get_random_user_agent():
    """
    获取随机的User-Agent
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70"
    ]
    return random.choice(user_agents)

def debug_query():
    """
    使用高级反爬策略调试查询
    """
    logger.info("开始使用高级反爬策略调试查询")
    
    try:
        # 创建会话
        session = requests.Session()
        
        # 1. 访问首页
        logger.info("1. 访问12306首页...")
        index_url = "https://kyfw.12306.cn/"
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\""
        }
        
        index_response = session.get(index_url, headers=headers)
        logger.info(f"首页访问成功，状态码: {index_response.status_code}")
        
        # 随机等待一段时间
        time.sleep(random.uniform(1, 3))
        
        # 2. 访问余票查询页面
        logger.info("2. 访问余票查询页面...")
        left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
        left_ticket_response = session.get(left_ticket_url, headers=headers)
        logger.info(f"余票查询页面访问成功，状态码: {left_ticket_response.status_code}")
        
        # 随机等待一段时间
        time.sleep(random.uniform(1, 3))
        
        # 3. 发送查询请求
        logger.info("3. 发送查询请求...")
        query_url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": "2026-02-20",
            "leftTicketDTO.from_station": "BHZ",  # 北海
            "leftTicketDTO.to_station": "GLZ",    # 桂林
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
        debug_file = "debug_anti_crawl.html"
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
            # 检查是否是反爬页面
            if "网络可能存在问题" in query_response.text:
                logger.error("12306返回了反爬页面")
            elif "DOCTYPE html" in query_response.text:
                logger.error("12306返回了HTML页面，可能是反爬")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_query()
