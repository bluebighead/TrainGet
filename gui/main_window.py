#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import sys
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QDateEdit, QComboBox, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QGroupBox, QProgressBar, QStatusBar,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import QDate, Qt, pyqtSignal, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont
from network.client import client
from parser.ticket_parser import parser
from scheduler.task_scheduler import scheduler
from exporter.exporter import export_to_excel, export_to_csv
from logger.logger import setup_logger
from utils.station_parser import station_parser

# 设置日志
logger = setup_logger()


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号定义
    update_result = pyqtSignal(list)
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("车票自动获取工具V1.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # 初始化变量
        self.query_results = []
        self.scheduled_task_id = None
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建查询条件区域
        self.create_query_section(main_layout)
        
        # 创建结果展示区域
        self.create_result_section(main_layout)
        
        # 创建操作控制区域
        self.create_control_section(main_layout)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请先检测网络连接")
        
        # 连接信号
        self.update_result.connect(self.display_results)
        self.update_status.connect(self.status_bar.showMessage)
        self.update_progress.connect(self.progress_bar.setValue)
        
        # 初始化时禁用所有按钮，只启用网络检测按钮
        self.disable_all_buttons()
        # 启用网络检测按钮
        self.test_network_button.setEnabled(True)
        
        # 显示法律安全说明
        self.show_legal_notice()
    
    def create_query_section(self, layout):
        """
        创建查询条件区域
        
        Args:
            layout: 父布局
        """
        # 创建查询条件组
        query_group = QGroupBox("查询条件")
        query_layout = QFormLayout()
        
        # 创建控件
        # 出发地选择（二级联动）
        self.start_city = QComboBox()
        self.start_city.setEditable(True)
        self.start_city.setPlaceholderText("如：北京")
        
        self.start_station = QComboBox()
        self.start_station.setEditable(True)
        self.start_station.setPlaceholderText("如：北京站")
        
        # 目的地选择（二级联动）
        self.end_city = QComboBox()
        self.end_city.setEditable(True)
        self.end_city.setPlaceholderText("如：上海")
        
        self.end_station = QComboBox()
        self.end_station.setEditable(True)
        self.end_station.setPlaceholderText("如：上海虹桥")
        
        # 添加城市列表
        cities = station_parser.get_cities()
        logger.info(f"在城市下拉框中添加了 {len(cities)} 个城市")
        
        for city in cities:
            self.start_city.addItem(city)
            self.end_city.addItem(city)
        
        # 实现城市和站点的联动
        self.start_city.currentTextChanged.connect(self.on_start_city_changed)
        self.end_city.currentTextChanged.connect(self.on_end_city_changed)
        
        # 初始化站点列表（默认选择第一个城市）
        if cities:
            first_city = cities[0]
            start_stations = station_parser.get_stations_by_city(first_city)
            end_stations = station_parser.get_stations_by_city(first_city)
            
            for station in start_stations:
                self.start_station.addItem(station)
            
            for station in end_stations:
                self.end_station.addItem(station)
        
        self.query_date = QDateEdit()
        self.query_date.setDate(QDate.currentDate())
        self.query_date.setCalendarPopup(True)
        
        self.train_type = QComboBox()
        self.train_type.addItems(["全部", "高铁", "动车", "普通列车"])
        
        # 创建水平布局用于放置城市和站点选择框
        start_layout = QHBoxLayout()
        start_layout.addWidget(self.start_city)
        start_layout.addWidget(self.start_station)
        start_layout.setStretch(0, 1)
        start_layout.setStretch(1, 2)
        
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.end_city)
        end_layout.addWidget(self.end_station)
        end_layout.setStretch(0, 1)
        end_layout.setStretch(1, 2)
        
        # 添加到布局
        query_layout.addRow("出发地:", start_layout)
        query_layout.addRow("目的地:", end_layout)
        query_layout.addRow("出发日期:", self.query_date)
        query_layout.addRow("车次类型:", self.train_type)
        
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
    
    def create_result_section(self, layout):
        """
        创建结果展示区域
        
        Args:
            layout: 父布局
        """
        # 创建结果组
        result_group = QGroupBox("查询结果")
        result_layout = QVBoxLayout()
        
        # 创建表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels([
            "车次", "出发时间", "到达时间", "历时", 
            "出发站", "到达站", "日期", "余票信息"
        ])
        # 设置最后一列自动拉伸
        self.result_table.horizontalHeader().setStretchLastSection(True)
        # 设置表格自动调整行高
        from PyQt5.QtWidgets import QHeaderView
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置表格水平滚动条策略
        self.result_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        # 添加到布局
        result_layout.addWidget(self.result_table)
        result_layout.addWidget(self.progress_bar)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
    
    def create_control_section(self, layout):
        """
        创建操作控制区域
        
        Args:
            layout: 父布局
        """
        # 创建控制组
        control_group = QGroupBox("操作控制")
        control_layout = QHBoxLayout()
        
        # 创建按钮
        self.query_button = QPushButton("立即查询")
        self.query_button.clicked.connect(self.start_query)
        
        self.schedule_button = QPushButton("定时查询")
        self.schedule_button.clicked.connect(self.toggle_schedule)
        
        self.transfer_button = QPushButton("查询中转车次")
        self.transfer_button.clicked.connect(self.start_transfer_query)
        
        self.test_network_button = QPushButton("检测网络")
        self.test_network_button.clicked.connect(self.test_network)
        # 设置默认颜色为红色
        self.test_network_button.setStyleSheet("background-color: red; color: white;")
        
        self.export_excel_button = QPushButton("导出Excel")
        self.export_excel_button.clicked.connect(self.export_excel)
        self.export_excel_button.setEnabled(False)
        
        self.export_csv_button = QPushButton("导出CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setEnabled(False)
        
        self.clear_button = QPushButton("清空结果")
        self.clear_button.clicked.connect(self.clear_results)
        
        self.help_button = QPushButton("使用说明")
        self.help_button.clicked.connect(self.show_help)
        
        # 添加到布局
        control_layout.addWidget(self.query_button)
        control_layout.addWidget(self.schedule_button)
        control_layout.addWidget(self.transfer_button)
        control_layout.addWidget(self.test_network_button)
        control_layout.addWidget(self.export_excel_button)
        control_layout.addWidget(self.export_csv_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.help_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
    
    def start_query(self):
        """
        开始查询
        """
        # 获取查询参数
        start_station = self.start_station.currentText().strip()
        end_station = self.end_station.currentText().strip()
        query_date = self.query_date.date().toString("yyyy-MM-dd")
        train_type = self.train_type.currentText()
        
        # 验证参数
        if not start_station or not end_station:
            QMessageBox.warning(self, "警告", "请输入出发地和目的地")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.update_progress.emit(20)
        
        # 在新线程中执行查询
        thread = threading.Thread(
            target=self.query_tickets,
            args=(start_station, end_station, query_date, train_type)
        )
        thread.daemon = True
        thread.start()
    
    def on_start_city_changed(self, city_name):
        """
        出发城市选择变化时更新站点列表
        
        Args:
            city_name: 选中的城市名称
        """
        # 清空当前站点列表
        self.start_station.clear()
        
        # 添加该城市的所有站点
        stations = station_parser.get_stations_by_city(city_name)
        for station in stations:
            self.start_station.addItem(station)
        
        logger.info(f"更新了出发城市 {city_name} 的站点列表，共 {len(stations)} 个站点")
    
    def on_end_city_changed(self, city_name):
        """
        目的城市选择变化时更新站点列表
        
        Args:
            city_name: 选中的城市名称
        """
        # 清空当前站点列表
        self.end_station.clear()
        
        # 添加该城市的所有站点
        stations = station_parser.get_stations_by_city(city_name)
        for station in stations:
            self.end_station.addItem(station)
        
        logger.info(f"更新了目的城市 {city_name} 的站点列表，共 {len(stations)} 个站点")
    
    def start_transfer_query(self):
        """
        开始查询中转车次
        """
        # 获取查询参数
        start_station = self.start_station.currentText().strip()
        end_station = self.end_station.currentText().strip()
        query_date = self.query_date.date().toString("yyyy-MM-dd")
        
        # 验证参数
        if not start_station or not end_station:
            QMessageBox.warning(self, "警告", "请输入出发地和目的地")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.update_progress.emit(20)
        
        # 在新线程中执行查询
        thread = threading.Thread(
            target=self.query_transfer_tickets,
            args=(start_station, end_station, query_date)
        )
        thread.daemon = True
        thread.start()
    
    def query_tickets(self, start_station, end_station, query_date, train_type):
        """
        查询车票
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
            train_type: 车次类型
        """
        try:
            self.update_status.emit("正在查询...")
            self.update_progress.emit(20)
            
            # 首先访问首页，获取cookie和会话信息
            logger.info("1. 访问12306首页获取会话信息...")
            index_url = "https://kyfw.12306.cn/"
            index_response = client.get(index_url)
            logger.info(f"首页访问成功，状态码: {index_response.status_code}")
            
            self.update_progress.emit(30)
            
            # 然后访问余票查询页面，获取更多会话信息
            logger.info("2. 访问余票查询页面获取会话信息...")
            left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
            left_ticket_response = client.get(left_ticket_url)
            logger.info(f"余票查询页面访问成功，状态码: {left_ticket_response.status_code}")
            
            self.update_progress.emit(40)
            
            # 获取站点编码
            from_station = client.get_station_code(start_station)
            to_station = client.get_station_code(end_station)
            
            # 检查站点编码是否有效
            if from_station == start_station:
                self.status_bar.showMessage(f"错误：出发站点 '{start_station}' 不存在")
                logger.error(f"出发站点 '{start_station}' 不存在")
                self.update_status.emit("查询失败：站点不存在")
                self.update_progress.emit(0)
                return
            if to_station == end_station:
                self.status_bar.showMessage(f"错误：到达站点 '{end_station}' 不存在")
                logger.error(f"到达站点 '{end_station}' 不存在")
                self.update_status.emit("查询失败：站点不存在")
                self.update_progress.emit(0)
                return
            
            # 构建查询URL（使用通用查询接口，支持所有类型车次）
            url = "https://kyfw.12306.cn/otn/leftTicket/query"
            params = {
                "leftTicketDTO.train_date": query_date,
                "leftTicketDTO.from_station": from_station,
                "leftTicketDTO.to_station": to_station,
                "purpose_codes": "ADULT"
            }
            
            # 添加额外的请求头，模拟真实浏览器
            extra_headers = {
                "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            # 随机等待一段时间，增加随机性
            import time
            import random
            time.sleep(random.uniform(2, 4))
            
            # 发送请求，使用最大重试次数
            try:
                response = client.get(url, params=params, headers=extra_headers, max_retries=3)
                
                # 保存响应内容到文件，以便调试
                debug_file = f"debug_gui_{start_station}_{end_station}_{query_date}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"响应内容已保存到 {debug_file}")
                
                # 解析JSON结果
                import json
                try:
                    result = response.json()
                    logger.info("JSON解析成功")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    # 尝试从响应中提取有用信息
                    if "网络可能存在问题" in response.text:
                        logger.error("12306返回了反爬页面")
                    elif "DOCTYPE html" in response.text:
                        logger.error("12306返回了HTML页面，可能是反爬")
                    # 记录响应内容的前200字符，避免编码错误
                    try:
                        # 尝试将响应内容转换为UTF-8编码，处理编码问题
                        response_content = response.text[:200]
                        # 使用repr()函数来显示原始字符串，避免编码错误
                        logger.error(f"响应内容前200字符: {repr(response_content)}")
                    except Exception as encode_error:
                        logger.error(f"记录响应内容时出现编码错误: {encode_error}")
                    raise
            except Exception as e:
                logger.error(f"网络请求失败: {e}")
                self.update_status.emit("查询失败：网络请求错误")
                self.update_progress.emit(0)
                self.status_bar.showMessage(f"查询失败：网络请求错误")
                raise
            
            # 处理查询结果
            tickets = []
            try:
                if not result:
                    logger.error("查询结果为空")
                    self.update_status.emit("查询结果为空")
                    self.update_result.emit([])
                    return
                
                if result.get("status"):
                    data = result.get("data", {})
                    if not data:
                        logger.error("查询结果中没有数据")
                        self.update_status.emit("查询结果中没有数据")
                        self.update_result.emit([])
                        return
                    
                    result_list = data.get("result", [])
                    if not result_list:
                        logger.info("查询结果为空，可能没有直达车次")
                        self.update_status.emit("查询结果为空，可能没有直达车次")
                        self.update_result.emit([])
                        return
                    
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
                            "软卧": fields[23] if fields[23] != "" else "无",
                            "站票": fields[26] if len(fields) > 26 and fields[26] != "" else "无"
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
                else:
                    error_message = result.get('messages', '未知错误')
                    logger.error(f"查询失败: {error_message}")
                    self.update_status.emit(f"查询失败: {error_message}")
                    self.update_result.emit([])
                    return
                
                # 过滤车次类型
                if train_type != "全部":
                    filtered_tickets = []
                    for ticket in tickets:
                        train_number = ticket["train_number"]
                        if train_type == "高铁" and (train_number.startswith("G") or train_number.startswith("C")):
                            filtered_tickets.append(ticket)
                        elif train_type == "动车" and train_number.startswith("D"):
                            filtered_tickets.append(ticket)
                        elif train_type == "普通列车" and not (train_number.startswith("G") or train_number.startswith("D") or train_number.startswith("C")):
                            filtered_tickets.append(ticket)
                    tickets = filtered_tickets
                
                self.update_progress.emit(80)
                self.update_result.emit(tickets)
                self.update_status.emit(f"查询完成，找到 {len(tickets)} 条记录")
            except Exception as e:
                logger.error(f"处理查询结果失败: {e}")
                self.update_status.emit("处理查询结果失败")
                self.update_result.emit([])
        except Exception as e:
            logger.error(f"查询失败: {e}")
            self.update_status.emit(f"查询失败: {str(e)}")
        finally:
            self.update_progress.emit(100)
            # 隐藏进度条
            self.progress_bar.setVisible(False)
    
    def query_transfer_tickets(self, start_station, end_station, query_date):
        """
        查询中转车次
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
        """
        try:
            self.update_status.emit("正在查询中转车次...")
            self.update_progress.emit(20)
            
            # 首先访问首页，获取cookie和会话信息
            logger.info("1. 访问12306首页获取会话信息...")
            index_url = "https://kyfw.12306.cn/"
            index_response = client.get(index_url)
            logger.info(f"首页访问成功，状态码: {index_response.status_code}")
            
            self.update_progress.emit(30)
            
            # 然后访问余票查询页面，获取更多会话信息
            logger.info("2. 访问余票查询页面获取会话信息...")
            left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
            left_ticket_response = client.get(left_ticket_url)
            logger.info(f"余票查询页面访问成功，状态码: {left_ticket_response.status_code}")
            
            self.update_progress.emit(40)
            
            # 获取站点编码
            from_station = client.get_station_code(start_station)
            to_station = client.get_station_code(end_station)
            
            # 检查站点编码是否有效
            if from_station == start_station:
                self.status_bar.showMessage(f"错误：出发站点 '{start_station}' 不存在")
                logger.error(f"出发站点 '{start_station}' 不存在")
                self.update_status.emit("查询失败：站点不存在")
                self.update_progress.emit(0)
                return
            if to_station == end_station:
                self.status_bar.showMessage(f"错误：到达站点 '{end_station}' 不存在")
                logger.error(f"到达站点 '{end_station}' 不存在")
                self.update_status.emit("查询失败：站点不存在")
                self.update_progress.emit(0)
                return
            
            self.update_progress.emit(60)
            
            # 查询中转车次
            logger.info(f"3. 查询中转车次: {start_station} -> {end_station}")
            transfer_plans = client.query_transfer_tickets(start_station, end_station, query_date)
            
            self.update_progress.emit(80)
            
            if not transfer_plans:
                logger.warning("未找到符合条件的中转车次")
                self.update_status.emit("未找到符合条件的中转车次")
                self.update_progress.emit(100)
                self.display_transfer_results([])
                return
            
            # 更新UI
            self.display_transfer_results(transfer_plans)
            self.update_status.emit(f"查询完成，找到 {len(transfer_plans)} 个中转方案")
            self.update_progress.emit(100)
            
        except Exception as e:
            logger.error(f"查询中转车次失败: {e}")
            self.update_status.emit(f"查询失败: {str(e)}")
        finally:
            self.update_progress.emit(100)
            # 隐藏进度条
            self.progress_bar.setVisible(False)
    
    def display_results(self, tickets):
        """
        显示查询结果
        
        Args:
            tickets: 车票信息列表
        """
        # 保存结果
        self.query_results = tickets
        
        # 清空表格
        self.result_table.setRowCount(0)
        
        # 填充表格
        for ticket in tickets:
            row_position = self.result_table.rowCount()
            self.result_table.insertRow(row_position)
            
            # 填充数据
            self.result_table.setItem(row_position, 0, QTableWidgetItem(ticket["train_number"]))
            self.result_table.setItem(row_position, 1, QTableWidgetItem(ticket["start_time"]))
            self.result_table.setItem(row_position, 2, QTableWidgetItem(ticket["end_time"]))
            self.result_table.setItem(row_position, 3, QTableWidgetItem(ticket["duration"]))
            self.result_table.setItem(row_position, 4, QTableWidgetItem(ticket["start_station"]))
            self.result_table.setItem(row_position, 5, QTableWidgetItem(ticket["end_station"]))
            self.result_table.setItem(row_position, 6, QTableWidgetItem(ticket["date"]))
            
            # 格式化余票信息
            remaining_info = "\n".join([f"{k}: {v}" for k, v in ticket["remaining_tickets"].items() if v])
            self.result_table.setItem(row_position, 7, QTableWidgetItem(remaining_info))
        
        # 启用导出按钮
        self.export_excel_button.setEnabled(len(tickets) > 0)
        self.export_csv_button.setEnabled(len(tickets) > 0)
        
        # 调整列宽
        self.result_table.resizeColumnsToContents()
    
    def display_transfer_results(self, transfer_plans):
        """
        显示中转车次结果
        
        Args:
            transfer_plans: 中转车次计划列表
        """
        from PyQt5.QtGui import QColor, QFont
        
        # 保存结果
        self.query_results = transfer_plans
        
        # 清空表格
        self.result_table.setRowCount(0)
        
        # 填充表格
        for plan_idx, plan in enumerate(transfer_plans):
            # 为每个中转方案创建多行
            for i, transfer in enumerate(plan["transfers"]):
                row_position = self.result_table.rowCount()
                self.result_table.insertRow(row_position)
                
                # 填充数据
                self.result_table.setItem(row_position, 0, QTableWidgetItem(transfer["train_number"]))
                self.result_table.setItem(row_position, 1, QTableWidgetItem(transfer["start_time"]))
                self.result_table.setItem(row_position, 2, QTableWidgetItem(transfer["end_time"]))
                self.result_table.setItem(row_position, 3, QTableWidgetItem(transfer["duration"]))
                self.result_table.setItem(row_position, 4, QTableWidgetItem(transfer["start_station"]))
                self.result_table.setItem(row_position, 5, QTableWidgetItem(transfer["end_station"]))
                self.result_table.setItem(row_position, 6, QTableWidgetItem(plan["date"]))
                
                # 格式化余票信息
                remaining_info = "\n".join([f"{k}: {v}" for k, v in transfer["remaining_tickets"].items() if v])
                self.result_table.setItem(row_position, 7, QTableWidgetItem(remaining_info))
                
                # 设置行背景颜色，区分不同的中转方案
                if plan_idx % 2 == 0:
                    for col in range(self.result_table.columnCount()):
                        item = self.result_table.item(row_position, col)
                        if item:
                            item.setBackground(QColor(245, 245, 245))
            
            # 添加中转信息行
            row_position = self.result_table.rowCount()
            self.result_table.insertRow(row_position)
            
            # 设置中转信息行的样式
            font = QFont()
            font.setBold(True)
            
            # 填充中转信息
            transfer_info_item = QTableWidgetItem("中转信息")
            transfer_info_item.setFont(font)
            self.result_table.setItem(row_position, 0, transfer_info_item)
            
            total_duration_item = QTableWidgetItem(f"总历时: {plan['total_duration']}")
            total_duration_item.setFont(font)
            self.result_table.setItem(row_position, 3, total_duration_item)
            
            transfer_station_item = QTableWidgetItem(f"中转站: {plan['transfer_station']}")
            transfer_station_item.setFont(font)
            self.result_table.setItem(row_position, 4, transfer_station_item)
            
            transfer_time_item = QTableWidgetItem(f"中转时间: {plan['transfer_time']}")
            transfer_time_item.setFont(font)
            self.result_table.setItem(row_position, 5, transfer_time_item)
            
            # 设置中转信息行的背景颜色
            for col in range(self.result_table.columnCount()):
                if self.result_table.item(row_position, col):
                    self.result_table.item(row_position, col).setBackground(QColor(220, 240, 255))
        
        # 启用导出按钮
        self.export_excel_button.setEnabled(len(transfer_plans) > 0)
        self.export_csv_button.setEnabled(len(transfer_plans) > 0)
        
        # 调整列宽
        self.result_table.resizeColumnsToContents()
        
        # 设置表格自动排序
        self.result_table.setSortingEnabled(True)
    
    def toggle_schedule(self):
        """
        切换定时查询状态
        """
        if self.scheduled_task_id:
            # 停止定时查询
            scheduler.remove_task(self.scheduled_task_id)
            self.scheduled_task_id = None
            self.schedule_button.setText("定时查询")
            self.update_status.emit("定时查询已停止")
        else:
            # 开始定时查询
            start_station = self.start_station.currentText().strip()
            end_station = self.end_station.currentText().strip()
            
            if not start_station or not end_station:
                QMessageBox.warning(self, "警告", "请输入出发地和目的地")
                return
            
            # 添加定时任务
            def scheduled_query():
                # 保存当前查询参数
                query_date = self.query_date.date().toString("yyyy-MM-dd")
                train_type = self.train_type.currentText()
                
                # 使用QMetaObject.invokeMethod在主线程中执行查询
                QMetaObject.invokeMethod(self, "query_tickets", 
                                       Qt.QueuedConnection, 
                                       Q_ARG(str, start_station),
                                       Q_ARG(str, end_station),
                                       Q_ARG(str, query_date),
                                       Q_ARG(str, train_type))
            
            self.scheduled_task_id = scheduler.add_task(300, scheduled_query)  # 5分钟查询一次
            scheduler.start()
            self.schedule_button.setText("停止定时查询")
            self.update_status.emit("定时查询已启动，每5分钟执行一次")
    
    def export_excel(self):
        """
        导出为Excel
        """
        if not self.query_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "tickets", "Excel files (*.xlsx)"
        )
        
        if file_path:
            try:
                export_to_excel(self.query_results, file_path)
                QMessageBox.information(self, "成功", f"已导出到: {file_path}")
            except Exception as e:
                logger.error(f"导出Excel失败: {e}")
                QMessageBox.error(self, "错误", f"导出失败: {str(e)}")
    
    def export_csv(self):
        """
        导出为CSV
        """
        if not self.query_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "tickets", "CSV files (*.csv)"
        )
        
        if file_path:
            try:
                export_to_csv(self.query_results, file_path)
                QMessageBox.information(self, "成功", f"已导出到: {file_path}")
            except Exception as e:
                logger.error(f"导出CSV失败: {e}")
                QMessageBox.error(self, "错误", f"导出失败: {str(e)}")
    
    def clear_results(self):
        """
        清空结果
        """
        self.result_table.setRowCount(0)
        self.query_results = []
        self.export_excel_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        self.update_status.emit("结果已清空")
    
    def disable_all_buttons(self):
        """
        禁用所有按钮
        """
        # 禁用查询按钮
        self.query_button.setEnabled(False)
        # 禁用定时查询按钮
        self.schedule_button.setEnabled(False)
        # 禁用中转查询按钮
        self.transfer_button.setEnabled(False)
        # 禁用导出Excel按钮
        self.export_excel_button.setEnabled(False)
        # 禁用导出CSV按钮
        self.export_csv_button.setEnabled(False)
        # 禁用清空结果按钮
        self.clear_button.setEnabled(False)
        # 禁用查询条件控件
        self.start_city.setEnabled(False)
        self.start_station.setEnabled(False)
        self.end_city.setEnabled(False)
        self.end_station.setEnabled(False)
        self.query_date.setEnabled(False)
        self.train_type.setEnabled(False)
        # 启用使用说明按钮
        self.help_button.setEnabled(True)
    
    def enable_all_buttons(self):
        """
        启用所有按钮
        """
        # 启用查询按钮
        self.query_button.setEnabled(True)
        # 启用定时查询按钮
        self.schedule_button.setEnabled(True)
        # 启用中转查询按钮
        self.transfer_button.setEnabled(True)
        # 启用导出Excel按钮（需要有查询结果才真正启用）
        self.export_excel_button.setEnabled(False)
        # 启用导出CSV按钮（需要有查询结果才真正启用）
        self.export_csv_button.setEnabled(False)
        # 启用清空结果按钮
        self.clear_button.setEnabled(True)
        # 启用查询条件控件
        self.start_city.setEnabled(True)
        self.start_station.setEnabled(True)
        self.end_city.setEnabled(True)
        self.end_station.setEnabled(True)
        self.query_date.setEnabled(True)
        self.train_type.setEnabled(True)
        # 启用使用说明按钮
        self.help_button.setEnabled(True)
    
    def test_network(self):
        """
        检测网络连通性
        """
        import socket
        import requests
        
        try:
            # 显示检测中状态
            self.status_bar.showMessage("正在检测网络连通性...")
            
            # 检测本地网络连接
            local_network_status = "正常"
            try:
                # 尝试连接到DNS服务器
                socket.create_connection(("8.8.8.8", 53), timeout=5)
            except Exception as e:
                local_network_status = f"异常: {str(e)}"
            
            # 检测12306网站是否可访问
            website_status = "正常"
            try:
                # 访问12306首页
                response = requests.get("https://kyfw.12306.cn", timeout=10)
                if response.status_code == 200:
                    website_status = "正常"
                else:
                    website_status = f"异常: 状态码 {response.status_code}"
            except Exception as e:
                website_status = f"异常: {str(e)}"
            
            # 显示检测结果
            result_message = f"网络检测结果:\n\n本地网络连接: {local_network_status}\n12306网站访问: {website_status}"
            self.status_bar.showMessage("网络检测完成")
            QMessageBox.information(self, "网络检测结果", result_message)
            
            # 根据检测结果修改按钮颜色和状态
            if local_network_status == "正常" and website_status == "正常":
                # 网络连通成功，改为绿色
                self.test_network_button.setStyleSheet("background-color: green; color: white;")
                # 启用所有按钮
                self.enable_all_buttons()
                # 更新状态栏信息
                self.status_bar.showMessage("就绪 - 网络连接正常")
            else:
                # 网络连通失败，保持红色
                self.test_network_button.setStyleSheet("background-color: red; color: white;")
                # 保持所有按钮禁用
                self.disable_all_buttons()
                # 重新启用网络检测按钮
                self.test_network_button.setEnabled(True)
                # 更新状态栏信息
                self.status_bar.showMessage("就绪 - 网络连接异常，请重新检测")
            
        except Exception as e:
            logger.error(f"网络检测失败: {e}")
            self.status_bar.showMessage("网络检测失败")
            QMessageBox.error(self, "错误", f"网络检测失败: {str(e)}")
            # 网络检测失败，保持红色
            self.test_network_button.setStyleSheet("background-color: red; color: white;")
            # 保持所有按钮禁用
            self.disable_all_buttons()
            # 重新启用网络检测按钮
            self.test_network_button.setEnabled(True)
            # 更新状态栏信息
            self.status_bar.showMessage("就绪 - 网络检测失败，请重新检测")
    
    def show_legal_notice(self):
        """
        显示法律安全说明
        """
        legal_message = """
法律安全说明

1. 本软件仅用于个人学习和研究目的，不得用于任何商业用途
2. 本软件使用12306官方接口获取数据，查询行为应遵守12306网站的使用条款
3. 请勿使用本软件进行频繁查询，以免对12306网站造成服务器负担
4. 本软件不对查询结果的准确性和时效性做出保证
5. 使用本软件即表示您同意以上条款
        """
        QMessageBox.warning(self, "法律安全说明", legal_message)
    
    def show_help(self):
        """
        显示使用说明
        """
        help_message = """
车票自动获取工具 V1.0

使用说明：
1. 启动软件后，请先点击"检测网络"按钮，确保网络连接正常
2. 选择出发城市和具体站点
3. 选择目的城市和具体站点
4. 选择出发日期
5. 选择车次类型（可选）
6. 点击"立即查询"按钮，获取直达车次信息
7. 点击"查询中转车次"按钮，获取中转车次信息
8. 查询结果可以导出为Excel或CSV格式

注意事项：
- 本软件使用12306官方接口获取车票信息
- 为避免被12306反爬机制限制，查询间隔会自动控制
- 如遇查询失败，请检查网络连接后重试

版本信息：
- 版本：V1.0
- 发布日期：2026-02-15
- 功能：直达车次查询、中转车次查询、网络检测
        """
        QMessageBox.information(self, "使用说明", help_message)
    
    def closeEvent(self, event):
        """
        关闭事件
        """
        # 停止定时任务
        if self.scheduled_task_id:
            scheduler.remove_task(self.scheduled_task_id)
        scheduler.stop()
        
        # 关闭网络客户端
        client.close()
        
        event.accept()
