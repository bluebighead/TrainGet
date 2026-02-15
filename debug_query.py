#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试车票查询功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network.client import NetworkClient
from logger.logger import setup_logger

# 初始化网络客户端
client = NetworkClient()

# 设置日志
logger = setup_logger()

def debug_query(start_station, end_station, query_date, train_type):
    """
    调试车票查询
    
    Args:
        start_station: 出发地
        end_station: 目的地
        query_date: 查询日期
        train_type: 车次类型
    """
    logger.info(f"开始调试查询: {start_station} -> {end_station}, 日期: {query_date}, 类型: {train_type}")
    
    try:
        # 1. 首先访问首页，获取cookie和会话信息
        logger.info("1. 访问12306首页获取会话信息...")
        index_url = "https://kyfw.12306.cn/"
        index_response = client.get(index_url)
        logger.info(f"首页访问成功，状态码: {index_response.status_code}")
        logger.info(f"首页响应头: {dict(index_response.headers)}")
        logger.info(f"首页Cookie: {index_response.cookies}")
        
        # 2. 获取站点编码
        logger.info("2. 获取站点编码...")
        from_station = client.get_station_code(start_station)
        to_station = client.get_station_code(end_station)
        logger.info(f"站点编码: {start_station} -> {from_station}, {end_station} -> {to_station}")
        
        # 3. 构建查询URL和参数
        logger.info("3. 构建查询参数...")
        url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": query_date,
            "leftTicketDTO.from_station": from_station,
            "leftTicketDTO.to_station": to_station,
            "purpose_codes": "ADULT"
        }
        logger.info(f"查询URL: {url}")
        logger.info(f"查询参数: {params}")
        
        # 4. 构建请求头
        logger.info("4. 构建请求头...")
        headers = {
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        logger.info(f"请求头: {headers}")
        
        # 5. 发送请求
        logger.info("5. 发送查询请求...")
        response = client.get(url, params=params, headers=headers)
        logger.info(f"请求成功，状态码: {response.status_code}")
        logger.info(f"响应头: {dict(response.headers)}")
        logger.info(f"响应内容长度: {len(response.text)}")
        
        # 保存响应内容到文件
        debug_file = f"debug_{start_station}_{end_station}_{query_date}.json"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"响应内容已保存到 {debug_file}")
        
        # 6. 解析响应内容
        logger.info("6. 解析响应内容...")
        try:
            result = response.json()
            logger.info(f"JSON解析成功")
            logger.info(f"响应状态: {result.get('status')}")
            logger.info(f"响应消息: {result.get('messages')}")
            logger.info(f"响应数据: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容: {response.text}")
            return []
        
        # 7. 处理查询结果
        logger.info("7. 处理查询结果...")
        tickets = []
        if result.get("status"):
            data = result.get("data", {})
            result_list = data.get("result", [])
            logger.info(f"原始结果数量: {len(result_list)}")
            
            for i, item in enumerate(result_list):
                logger.info(f"解析第 {i+1} 条记录: {item[:100]}...")
                # 解析车次信息
                fields = item.split("|")
                logger.info(f"字段数量: {len(fields)}")
                
                if len(fields) < 30:
                    logger.warning(f"字段数量不足，跳过: {item}")
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
                
                logger.info(f"车次: {train_number}, 出发: {start_station_name}({start_time}), 到达: {end_station_name}({end_time}), 历时: {duration}")
                
                # 解析余票信息
                remaining_tickets = {
                    "商务座": fields[32] if fields[32] != "" else "无",
                    "一等座": fields[31] if fields[31] != "" else "无",
                    "二等座": fields[30] if fields[30] != "" else "无",
                    "硬卧": fields[28] if fields[28] != "" else "无",
                    "硬座": fields[29] if fields[29] != "" else "无",
                    "软卧": fields[23] if fields[23] != "" else "无"
                }
                
                logger.info(f"余票信息: {remaining_tickets}")
                
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
        
        # 8. 过滤车次类型
        logger.info(f"8. 过滤车次类型: {train_type}")
        if train_type != "全部":
            filtered_tickets = []
            for ticket in tickets:
                train_number = ticket["train_number"]
                if train_type == "高铁" and train_number.startswith("G"):
                    filtered_tickets.append(ticket)
                elif train_type == "动车" and train_number.startswith("D"):
                    filtered_tickets.append(ticket)
                elif train_type == "普通列车" and not (train_number.startswith("G") or train_number.startswith("D")):
                    filtered_tickets.append(ticket)
            logger.info(f"过滤后剩余: {len(filtered_tickets)} 条")
            tickets = filtered_tickets
        
        # 9. 打印最终结果
        logger.info("9. 打印最终结果...")
        for ticket in tickets:
            logger.info(f"车次: {ticket['train_number']}")
            logger.info(f"出发: {ticket['start_station']} {ticket['start_time']}")
            logger.info(f"到达: {ticket['end_station']} {ticket['end_time']}")
            logger.info(f"历时: {ticket['duration']}")
            logger.info(f"余票: {ticket['remaining_tickets']}")
            logger.info("-" * 50)
        
        return tickets
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return []
    finally:
        # 关闭客户端
        client.close()

if __name__ == "__main__":
    # 测试案例1: 北京 -> 上海 (应该有很多车次)
    logger.info("=== 测试案例1: 北京 -> 上海 ===")
    debug_query("北京", "上海", "2026-02-16", "全部")
    
    # 测试案例2: 北海 -> 合浦 (用户反馈的问题)
    logger.info("\n=== 测试案例2: 北海 -> 合浦 ===")
    debug_query("北海", "合浦", "2026-02-16", "全部")
    
    # 测试案例3: 选择其他热门路线
    logger.info("\n=== 测试案例3: 广州 -> 深圳 ===")
    debug_query("广州", "深圳", "2026-02-16", "全部")
