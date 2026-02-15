#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车票信息解析模块
"""

import re
from bs4 import BeautifulSoup
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()


class TicketParser:
    """车票信息解析器"""
    
    def parse_ticket_info(self, html_content):
        """
        解析车票信息
        
        Args:
            html_content: HTML内容
        
        Returns:
            list: 车票信息列表
        """
        try:
            # 创建BeautifulSoup对象
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 查找所有表格，尝试不同的选择器
            tables = soup.find_all('table')
            logger.info(f"找到 {len(tables)} 个表格")
            
            # 遍历所有表格，寻找包含车票信息的表格
            ticket_table = None
            for i, table in enumerate(tables):
                # 检查表格是否包含车次信息
                if table.find('tr') and table.find(text=re.compile(r'[GDCTKZ]\d+')):
                    ticket_table = table
                    logger.info(f"在第 {i+1} 个表格中找到车票信息")
                    break
            
            # 如果没有找到，尝试查找包含特定类的表格
            if not ticket_table:
                ticket_table = soup.find('table', class_=re.compile(r'.*result.*|.*ticket.*|.*list.*'))
                if ticket_table:
                    logger.info("通过类名找到车票信息表格")
            
            if not ticket_table:
                logger.warning("未找到车票信息表格")
                # 保存页面内容到文件，以便调试
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info("页面内容已保存到 debug_page.html 以供调试")
                return []
            
            # 查找表格行
            rows = ticket_table.find_all('tr')
            if not rows:
                logger.warning("未找到车票信息行")
                return []
            
            ticket_list = []
            
            # 遍历表格行，跳过表头
            for row in rows[1:]:
                ticket_info = self._parse_row(row)
                if ticket_info:
                    ticket_list.append(ticket_info)
            
            logger.info(f"成功解析 {len(ticket_list)} 条车票信息")
            return ticket_list
            
        except Exception as e:
            logger.error(f"解析车票信息失败: {e}")
            # 保存页面内容到文件，以便调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("页面内容已保存到 debug_page.html 以供调试")
            return []
    
    def _parse_row(self, row):
        """
        解析单行车票信息
        
        Args:
            row: 表格行元素
        
        Returns:
            dict: 车票信息字典
        """
        try:
            # 查找所有单元格
            cells = row.find_all('td')
            if len(cells) < 5:
                logger.warning("单元格数量不足")
                return None
            
            # 尝试从不同位置解析车次信息
            train_number = ""
            for i, cell in enumerate(cells):
                # 查找车次信息
                train_match = re.search(r'([GDCTKZ]\d+)', cell.text)
                if train_match:
                    train_number = train_match.group(1)
                    logger.info(f"在第 {i+1} 个单元格找到车次: {train_number}")
                    break
            
            if not train_number:
                logger.warning("未找到车次信息")
                return None
            
            # 尝试解析时间和站点信息
            start_time = ""
            end_time = ""
            duration = ""
            start_station = ""
            end_station = ""
            date_info = ""
            
            # 遍历单元格，尝试提取信息
            for i, cell in enumerate(cells):
                cell_text = cell.text.strip()
                
                # 尝试匹配时间格式
                time_match = re.search(r'\d{2}:\d{2}', cell_text)
                if time_match:
                    if not start_time:
                        start_time = time_match.group(0)
                    elif not end_time:
                        end_time = time_match.group(0)
                
                # 尝试匹配历时
                duration_match = re.search(r'\d+小时\d+分|\d+分', cell_text)
                if duration_match:
                    duration = duration_match.group(0)
                
                # 尝试提取站点信息
                if '站' in cell_text and len(cell_text) > 1:
                    if not start_station:
                        start_station = cell_text
                    elif not end_station:
                        end_station = cell_text
                
                # 尝试提取日期信息
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', cell_text)
                if date_match:
                    date_info = date_match.group(0)
            
            # 解析余票信息
            ticket_info = {
                "train_number": train_number,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "start_station": start_station,
                "end_station": end_station,
                "date": date_info,
                "remaining_tickets": {}
            }
            
            # 解析不同座位类型的余票
            seat_types = ['硬座', '硬卧', '软卧', '二等座', '一等座', '商务座']
            for i, cell in enumerate(cells):
                cell_text = cell.text.strip()
                for seat_type in seat_types:
                    if seat_type in cell_text:
                        # 尝试从相邻单元格获取余票信息
                        if i + 1 < len(cells):
                            remaining = cells[i + 1].text.strip()
                            ticket_info["remaining_tickets"][seat_type] = remaining
            
            # 如果余票信息为空，尝试从所有单元格中提取
            if not ticket_info["remaining_tickets"]:
                for i, cell in enumerate(cells):
                    cell_text = cell.text.strip()
                    # 检查是否包含余票信息
                    if re.search(r'\d+|无|有', cell_text) and len(cell_text) <= 5:
                        # 尝试推断座位类型
                        if i > 0:
                            prev_cell = cells[i-1].text.strip()
                            for seat_type in seat_types:
                                if seat_type in prev_cell:
                                    ticket_info["remaining_tickets"][seat_type] = cell_text
            
            logger.info(f"解析车次 {train_number} 成功")
            return ticket_info
            
        except Exception as e:
            logger.error(f"解析单行车票信息失败: {e}")
            return None
    
    def parse_station_code(self, html_content):
        """
        解析站点编码
        
        Args:
            html_content: HTML内容
        
        Returns:
            dict: 站点编码字典
        """
        try:
            # 查找站点编码信息
            station_code_match = re.search(r'var station_names = "([^"]+)"', html_content)
            if not station_code_match:
                logger.warning("未找到站点编码信息")
                return {}
            
            # 解析站点编码
            station_info = station_code_match.group(1)
            station_list = station_info.split('|')
            
            station_dict = {}
            for i in range(0, len(station_list), 5):
                if i + 1 < len(station_list):
                    station_name = station_list[i]
                    station_code = station_list[i + 1]
                    station_dict[station_name] = station_code
            
            logger.info(f"成功解析 {len(station_dict)} 个站点编码")
            return station_dict
            
        except Exception as e:
            logger.error(f"解析站点编码失败: {e}")
            return {}


# 创建全局解析器实例
parser = TicketParser()
