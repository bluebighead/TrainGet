#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试北海到来宾的查询
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network.client import NetworkClient
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def test_laibin_query():
    """
    测试北海到来宾的查询
    """
    logger.info("开始测试北海到来宾的查询")
    
    try:
        # 创建网络客户端
        client = NetworkClient()
        
        # 测试站点编码
        beihai_code = client.get_station_code("北海")
        laibin_code = client.get_station_code("来宾")
        
        logger.info(f"北海的站点编码: {beihai_code}")
        logger.info(f"来宾的站点编码: {laibin_code}")
        
        # 测试查询
        query_date = "2026-02-21"
        logger.info(f"查询日期: {query_date}")
        
        # 首先访问首页获取会话信息
        logger.info("1. 访问首页获取会话信息...")
        client.get("https://kyfw.12306.cn/")
        
        # 然后访问余票查询页面
        logger.info("2. 访问余票查询页面...")
        client.get("https://kyfw.12306.cn/otn/leftTicket/init")
        
        # 构建查询URL
        url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": query_date,
            "leftTicketDTO.from_station": beihai_code,
            "leftTicketDTO.to_station": laibin_code,
            "purpose_codes": "ADULT"
        }
        
        # 添加额外的请求头
        extra_headers = {
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        logger.info("3. 发送查询请求...")
        response = client.get(url, params=params, headers=extra_headers)
        logger.info(f"查询请求成功，状态码: {response.status_code}")
        
        # 保存响应内容到文件
        debug_file = f"debug_beihai_laibin_{query_date}.json"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"响应内容已保存到 {debug_file}")
        
        # 解析响应内容
        logger.info("4. 解析响应内容...")
        try:
            result = response.json()
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
                    
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容前500字符: {response.text[:500]}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    test_laibin_query()
