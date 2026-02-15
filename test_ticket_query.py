#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试车票查询功能
"""

import sys
import os
from network.client import client
from parser.ticket_parser import parser
from logger.logger import setup_logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logger = setup_logger()


def test_ticket_query():
    """
    测试车票查询功能
    """
    logger.info("开始测试车票查询功能...")
    
    try:
        # 首先访问首页，获取cookie和会话信息
        logger.info("访问12306首页获取会话信息...")
        index_url = "https://kyfw.12306.cn/"
        index_response = client.get(index_url)
        logger.info(f"首页访问成功，状态码: {index_response.status_code}")
        
        # 使用实际的查询参数
        start_station = "北京"
        end_station = "上海"
        query_date = "2026-02-16"  # 明天的日期
        
        # 获取站点编码
        from_station = client.get_station_code(start_station)
        to_station = client.get_station_code(end_station)
        
        # 构建查询URL（使用通用查询接口，支持所有类型车次）
        url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": query_date,
            "leftTicketDTO.from_station": from_station,
            "leftTicketDTO.to_station": to_station,
            "purpose_codes": "ADULT"
        }
        
        # 发送请求
        logger.info(f"查询 {start_station} 到 {end_station} 的车票，日期: {query_date}")
        # 添加额外的请求头，模拟真实浏览器
        extra_headers = {
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = client.get(url, params=params, headers=extra_headers)
        
        # 保存响应内容到文件
        with open('debug_response.json', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("响应内容已保存到 debug_response.json")
        
        # 检查响应内容
        if response.status_code == 200:
            logger.info(f"响应内容长度: {len(response.text)}")
            logger.info(f"响应内容前100字符: {response.text[:100]}")
        
        # 解析JSON结果
        import json
        result = response.json()
        
        # 处理查询结果
        tickets = []
        if result.get("status"):
            data = result.get("data", {})
            result_list = data.get("result", [])
            
            for item in result_list:
                # 解析车次信息
                fields = item.split("|")
                if len(fields) < 30:
                    continue
                
                train_number = fields[3]
                start_station_code = fields[6]
                end_station_code = fields[7]
                # 将站点编码转换为中文名称
                start_station_name = client.get_station_name(start_station_code)
                end_station_name = client.get_station_name(end_station_code)
                start_time = fields[8]
                end_time = fields[9]
                duration = fields[10]
                
                # 解析余票信息
                remaining_tickets = {
                    "商务座": fields[32] if fields[32] != "" else "无",
                    "一等座": fields[31] if fields[31] != "" else "无",
                    "二等座": fields[30] if fields[30] != "" else "无",
                    "硬卧": fields[28] if fields[28] != "" else "无",
                    "硬座": fields[29] if fields[29] != "" else "无",
                    "软卧": fields[23] if fields[23] != "" else "无"
                }
                
                ticket_info = {
                    "train_number": train_number,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "start_station": start_station_name,
                    "end_station": end_station_name,
                    "date": query_date,
                    "remaining_tickets": remaining_tickets
                }
                
                tickets.append(ticket_info)
        
        logger.info(f"解析到 {len(tickets)} 条车票信息")
        
        # 打印解析结果
        for ticket in tickets[:5]:  # 只打印前5条
            logger.info(f"车次: {ticket['train_number']}")
            logger.info(f"出发时间: {ticket['start_time']}")
            logger.info(f"到达时间: {ticket['end_time']}")
            logger.info(f"历时: {ticket['duration']}")
            logger.info(f"出发站: {ticket['start_station']}")
            logger.info(f"到达站: {ticket['end_station']}")
            logger.info(f"日期: {ticket['date']}")
            logger.info(f"余票信息: {ticket['remaining_tickets']}")
            logger.info("-" * 50)
        
        if len(tickets) > 5:
            logger.info(f"... 还有 {len(tickets) - 5} 条记录未显示")
        
        if not tickets:
            logger.warning("未解析到任何车票信息")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    test_ticket_query()
