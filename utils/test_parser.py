#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网络请求和网页解析功能
"""

from network.client import client
from parser.ticket_parser import parser
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()


def test_network_and_parser():
    """测试网络请求和网页解析功能"""
    try:
        # 测试URL
        test_url = "https://kyfw.12306.cn/otn/leftTicket/init"
        
        # 发送请求
        logger.info("测试网络请求...")
        response = client.get(test_url)
        
        # 解析站点编码
        logger.info("测试站点编码解析...")
        station_dict = parser.parse_station_code(response.text)
        logger.info(f"解析到站点数量: {len(station_dict)}")
        
        # 打印前10个站点
        if station_dict:
            logger.info("前10个站点:")
            for i, (station, code) in enumerate(list(station_dict.items())[:10]):
                logger.info(f"{i+1}. {station}: {code}")
        
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    test_network_and_parser()
