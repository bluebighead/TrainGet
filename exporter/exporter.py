#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出模块
"""

import pandas as pd
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()


def export_to_excel(tickets, file_path):
    """
    导出车票信息到Excel文件
    
    Args:
        tickets: 车票信息列表
        file_path: 保存路径
    """
    try:
        # 准备数据
        data = []
        for ticket in tickets:
            # 提取基本信息
            row = {
                "车次": ticket["train_number"],
                "出发时间": ticket["start_time"],
                "到达时间": ticket["end_time"],
                "历时": ticket["duration"],
                "出发站": ticket["start_station"],
                "到达站": ticket["end_station"],
                "日期": ticket["date"]
            }
            
            # 添加余票信息
            row.update(ticket["remaining_tickets"])
            data.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 导出到Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='车票信息')
        
        logger.info(f"成功导出 {len(tickets)} 条车票信息到Excel: {file_path}")
        
    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        raise


def export_to_csv(tickets, file_path):
    """
    导出车票信息到CSV文件
    
    Args:
        tickets: 车票信息列表
        file_path: 保存路径
    """
    try:
        # 准备数据
        data = []
        for ticket in tickets:
            # 提取基本信息
            row = {
                "车次": ticket["train_number"],
                "出发时间": ticket["start_time"],
                "到达时间": ticket["end_time"],
                "历时": ticket["duration"],
                "出发站": ticket["start_station"],
                "到达站": ticket["end_station"],
                "日期": ticket["date"]
            }
            
            # 添加余票信息
            row.update(ticket["remaining_tickets"])
            data.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 导出到CSV
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"成功导出 {len(tickets)} 条车票信息到CSV: {file_path}")
        
    except Exception as e:
        logger.error(f"导出CSV失败: {e}")
        raise
