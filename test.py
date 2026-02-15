#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本
"""

import sys
import os
from network.client import client
from parser.ticket_parser import parser
from scheduler.task_scheduler import scheduler
from exporter.exporter import export_to_excel, export_to_csv
from logger.logger import setup_logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logger = setup_logger()


def test_network():
    """
    测试网络请求模块
    """
    logger.info("开始测试网络请求模块...")
    try:
        # 测试GET请求
        url = "https://kyfw.12306.cn/"
        response = client.get(url)
        logger.info(f"GET请求成功，状态码: {response.status_code}")
        
        # 测试POST请求
        url = "https://kyfw.12306.cn/otn/login/init"
        response = client.post(url)
        logger.info(f"POST请求成功，状态码: {response.status_code}")
        
        logger.info("网络请求模块测试通过")
        return True
    except Exception as e:
        logger.error(f"网络请求模块测试失败: {e}")
        return False


def test_parser():
    """
    测试网页解析模块
    """
    logger.info("开始测试网页解析模块...")
    try:
        # 获取测试页面
        url = "https://kyfw.12306.cn/otn/leftTicket/init"
        response = client.get(url)
        
        # 测试站点编码解析
        station_dict = parser.parse_station_code(response.text)
        logger.info(f"站点编码解析成功，解析到 {len(station_dict)} 个站点")
        
        # 测试车票信息解析
        tickets = parser.parse_ticket_info(response.text)
        logger.info(f"车票信息解析成功，解析到 {len(tickets)} 条记录")
        
        logger.info("网页解析模块测试通过")
        return True
    except Exception as e:
        logger.error(f"网页解析模块测试失败: {e}")
        return False


def test_scheduler():
    """
    测试定时任务模块
    """
    logger.info("开始测试定时任务模块...")
    try:
        # 测试添加任务
        def test_task():
            logger.info("定时任务执行测试")
        
        task_id = scheduler.add_task(5, test_task)
        logger.info(f"添加定时任务成功，任务ID: {task_id}")
        
        # 测试启动调度器
        scheduler.start()
        logger.info("调度器启动成功")
        
        # 等待任务执行
        import time
        time.sleep(6)
        
        # 测试移除任务
        scheduler.remove_task(task_id)
        logger.info("移除定时任务成功")
        
        # 测试停止调度器
        scheduler.stop()
        logger.info("调度器停止成功")
        
        logger.info("定时任务模块测试通过")
        return True
    except Exception as e:
        logger.error(f"定时任务模块测试失败: {e}")
        scheduler.stop()
        return False


def test_exporter():
    """
    测试数据导出模块
    """
    logger.info("开始测试数据导出模块...")
    try:
        # 准备测试数据
        test_tickets = [
            {
                "train_number": "G101",
                "start_time": "08:00",
                "end_time": "12:00",
                "duration": "04:00",
                "start_station": "北京",
                "end_station": "上海",
                "date": "2024-01-01",
                "remaining_tickets": {
                    "二等座": "有",
                    "一等座": "10",
                    "商务座": "2"
                }
            },
            {
                "train_number": "D201",
                "start_time": "09:00",
                "end_time": "13:30",
                "duration": "04:30",
                "start_station": "北京",
                "end_station": "上海",
                "date": "2024-01-01",
                "remaining_tickets": {
                    "二等座": "5",
                    "一等座": "0",
                    "商务座": "0"
                }
            }
        ]
        
        # 测试导出Excel
        excel_path = "test_tickets.xlsx"
        export_to_excel(test_tickets, excel_path)
        logger.info(f"Excel导出成功: {excel_path}")
        
        # 测试导出CSV
        csv_path = "test_tickets.csv"
        export_to_csv(test_tickets, csv_path)
        logger.info(f"CSV导出成功: {csv_path}")
        
        logger.info("数据导出模块测试通过")
        return True
    except Exception as e:
        logger.error(f"数据导出模块测试失败: {e}")
        return False


def run_all_tests():
    """
    运行所有测试
    """
    logger.info("开始运行所有测试...")
    
    tests = [
        ("网络请求模块", test_network),
        ("网页解析模块", test_parser),
        ("定时任务模块", test_scheduler),
        ("数据导出模块", test_exporter)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n测试: {test_name}")
        if test_func():
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n测试完成: 共 {len(tests)} 个测试，通过 {passed} 个，失败 {failed} 个")
    
    # 清理测试文件
    for file_path in ["test_tickets.xlsx", "test_tickets.csv"]:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"清理测试文件: {file_path}")


if __name__ == "__main__":
    run_all_tests()
