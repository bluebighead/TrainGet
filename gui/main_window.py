#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import sys
import threading
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QDateEdit, QComboBox, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QGroupBox, QProgressBar, QStatusBar,
    QMessageBox, QFileDialog, QTextEdit, QFrame, QDialog, QCheckBox, QSpinBox,
    QHeaderView, QApplication, QCompleter
)
from PyQt5.QtCore import QDate, Qt, pyqtSignal, QMetaObject, Q_ARG, QTimer, QEvent
from PyQt5.QtGui import QFont
from network.client import client
from parser.ticket_parser import parser
from scheduler.task_scheduler import scheduler
from exporter.exporter import export_to_excel, export_to_csv
from logger.logger import setup_logger
from utils.station_parser import station_parser

# 设置日志
logger = setup_logger()

# 自定义事件类，用于更新车次表格
class UpdateTrainTableEvent(QEvent):
    def __init__(self, trains):
        super().__init__(QEvent.User)
        self.trains = trains


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号定义
    update_result = pyqtSignal(list)
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    update_query_count_signal = pyqtSignal(int)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("车票自动获取工具V1.0")
        self.setGeometry(100, 100, 1080, 768)
        
        # 设置全局样式
        self.setStyleSheet("""
            /* 主窗口背景 */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* 标签样式 */
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            
            /* 标题标签 */
            QLabel#title_label {
                font-size: 20px;
                font-weight: bold;
                color: #1E88E5;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #1E88E5;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                border: none;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #1565C0;
            }
            
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            
            /* 输入框样式 */
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                border-color: #1E88E5;
                outline: none;
            }
            
            /* 复选框样式 */
            QCheckBox {
                font-size: 14px;
                color: #333333;
            }
            
            /* 分组框样式 */
            QGroupBox {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: white;
                color: #1E88E5;
                font-weight: bold;
            }
            
            /* 表格样式 */
            QTableWidget {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #F5F5F5;
            }
            
            QTableWidget::item {
                padding: 8px;
                font-size: 13px;
            }
            
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1565C0;
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #F5F5F5;
                height: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #BDBDBD;
                border-radius: 5px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #9E9E9E;
            }
            
            /* 进度条样式 */
            QProgressBar {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                background-color: #F5F5F5;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #1E88E5;
                border-radius: 3px;
            }
            
            /* 状态栏样式 */
            QStatusBar {
                background-color: white;
                border-top: 1px solid #DDDDDD;
            }
        """)
        
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
        
        # 自动盯票相关变量
        self.auto_track_thread = None
        self.auto_track_running = False
        self.auto_track_config = {
            'train_types': [],
            'seat_classes': [],
            'interval': 60,
            'start_station': '',
            'end_station': '',
            'query_date': '',
            'selected_trains': [],
            'email_alert': False,
            'email_address': '',
            'email_password': '',
            'remember_email': False
        }
        # 查询次数计数器
        self.query_count = 0
        # 车次数据
        self.all_trains = []
        # 创建自动盯票状态标签
        self.auto_track_status_label = QLabel("自动盯票: 未启动")
        # 连接信号到槽函数
        self.update_query_count_signal.connect(self.update_query_count)
        self.auto_track_status_label.setStyleSheet("color: gray;")
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # 添加自动盯票状态标签
        self.status_bar.addPermanentWidget(self.auto_track_status_label)
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
        
        # 加载保存的设置
        self.load_settings()
    
    def create_query_section(self, layout):
        """
        创建查询条件区域
        
        Args:
            layout: 父布局
        """
        # 创建标题标签
        title_label = QLabel("12306 余票查询")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建查询条件组
        query_group = QGroupBox("查询条件")
        query_layout = QFormLayout()
        
        # 设置布局间距
        query_layout.setContentsMargins(20, 15, 20, 15)
        query_layout.setVerticalSpacing(15)
        
        # 创建控件
        # 出发地选择（二级联动）
        self.start_city = QComboBox()
        self.start_city.setEditable(True)
        self.start_city.setPlaceholderText("如：北京")
        self.start_city.setInsertPolicy(QComboBox.NoInsert)
        self.start_city.setMinimumWidth(120)
        
        self.start_station = QComboBox()
        self.start_station.setEditable(True)
        self.start_station.setPlaceholderText("如：北京站")
        self.start_station.setInsertPolicy(QComboBox.NoInsert)
        self.start_station.setMinimumWidth(200)
        
        # 目的地选择（二级联动）
        self.end_city = QComboBox()
        self.end_city.setEditable(True)
        self.end_city.setPlaceholderText("如：上海")
        self.end_city.setInsertPolicy(QComboBox.NoInsert)
        self.end_city.setMinimumWidth(120)
        
        self.end_station = QComboBox()
        self.end_station.setEditable(True)
        self.end_station.setPlaceholderText("如：上海虹桥")
        self.end_station.setInsertPolicy(QComboBox.NoInsert)
        self.end_station.setMinimumWidth(200)
        
        # 添加城市列表
        cities = station_parser.get_cities()
        logger.info(f"在城市下拉框中添加了 {len(cities)} 个城市")
        
        for city in cities:
            self.start_city.addItem(city)
            self.end_city.addItem(city)
        
        # 为城市下拉框添加自动补全
        start_city_completer = QCompleter(cities)
        start_city_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.start_city.setCompleter(start_city_completer)
        
        end_city_completer = QCompleter(cities)
        end_city_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.end_city.setCompleter(end_city_completer)
        
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
            
            # 为站点下拉框添加自动补全
            start_station_completer = QCompleter(start_stations)
            start_station_completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.start_station.setCompleter(start_station_completer)
            
            end_station_completer = QCompleter(end_stations)
            end_station_completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.end_station.setCompleter(end_station_completer)
        
        self.query_date = QDateEdit()
        self.query_date.setDate(QDate.currentDate())
        self.query_date.setCalendarPopup(True)
        self.query_date.setMinimumWidth(150)
        
        self.train_type = QComboBox()
        self.train_type.addItems(["全部", "高铁", "动车", "普通列车"])
        self.train_type.setMinimumWidth(120)
        
        # 创建水平布局用于放置城市和站点选择框
        start_layout = QHBoxLayout()
        start_layout.addWidget(self.start_city)
        start_layout.addSpacing(10)
        start_layout.addWidget(self.start_station)
        start_layout.setStretch(0, 1)
        start_layout.setStretch(1, 2)
        
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.end_city)
        end_layout.addSpacing(10)
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
        layout.addSpacing(10)
    
    def create_result_section(self, layout):
        """
        创建结果展示区域
        
        Args:
            layout: 父布局
        """
        # 创建结果组
        result_group = QGroupBox("查询结果")
        result_layout = QVBoxLayout()
        
        # 设置布局间距
        result_layout.setContentsMargins(15, 15, 15, 15)
        result_layout.setSpacing(10)
        
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
        # 设置表格样式
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SingleSelection)
        # 设置表头样式
        header = self.result_table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #E3F2FD;
                color: #1565C0;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #DDDDDD;
            }
        """)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(20)
        
        # 添加到布局
        result_layout.addWidget(self.result_table)
        result_layout.addWidget(self.progress_bar)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        layout.addSpacing(10)
    
    def create_control_section(self, layout):
        """
        创建操作控制区域
        
        Args:
            layout: 父布局
        """
        # 创建控制组
        control_group = QGroupBox("操作控制")
        control_layout = QVBoxLayout()
        
        # 设置布局间距
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(10)
        
        # 创建按钮行
        button_layout1 = QHBoxLayout()
        button_layout2 = QHBoxLayout()
        info_layout = QHBoxLayout()
        
        # 创建按钮
        self.query_button = QPushButton("立即查询")
        self.query_button.clicked.connect(self.start_query)
        self.query_button.setMinimumWidth(100)
        
        self.schedule_button = QPushButton("定时查询")
        self.schedule_button.clicked.connect(self.toggle_schedule)
        self.schedule_button.setMinimumWidth(100)
        
        self.transfer_button = QPushButton("查询中转车次")
        self.transfer_button.clicked.connect(self.start_transfer_query)
        self.transfer_button.setMinimumWidth(120)
        
        self.test_network_button = QPushButton("检测网络")
        self.test_network_button.clicked.connect(self.test_network)
        # 设置默认颜色为红色
        self.test_network_button.setStyleSheet("background-color: red; color: white; border-radius: 4px; padding: 8px 16px;")
        self.test_network_button.setMinimumWidth(100)
        
        self.export_excel_button = QPushButton("导出Excel")
        self.export_excel_button.clicked.connect(self.export_excel)
        self.export_excel_button.setEnabled(False)
        self.export_excel_button.setMinimumWidth(100)
        
        self.export_csv_button = QPushButton("导出CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.setMinimumWidth(100)
        
        self.clear_button = QPushButton("清空结果")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setMinimumWidth(100)
        
        self.help_button = QPushButton("使用说明")
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setMinimumWidth(100)
        
        # 创建自动盯票按钮
        self.auto_track_button = QPushButton("自动盯票")
        self.auto_track_button.clicked.connect(self.show_auto_track_dialog)
        self.auto_track_button.setMinimumWidth(100)
        
        # 创建查询次数显示标签
        self.query_count_label = QLabel("查询次数: 0")
        self.query_count_label.setStyleSheet("font-weight: bold; color: #1E88E5; font-size: 14px;")
        
        self.clear_logs_button = QPushButton("清理日志")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        # 初始设置为灰色不可选状态
        self.clear_logs_button.setEnabled(False)
        self.clear_logs_button.setStyleSheet("background-color: gray; color: white; border-radius: 4px; padding: 8px 16px;")
        self.clear_logs_button.setMinimumWidth(100)
        
        # 创建夜晚模式切换按钮
        self.night_mode_button = QPushButton("夜晚模式")
        self.night_mode_button.clicked.connect(self.toggle_night_mode)
        # 初始化为白天模式
        self.is_night_mode = False
        self.night_mode_button.setMinimumWidth(100)
        
        # 添加按钮到布局
        button_layout1.addWidget(self.query_button)
        button_layout1.addSpacing(10)
        button_layout1.addWidget(self.schedule_button)
        button_layout1.addSpacing(10)
        button_layout1.addWidget(self.transfer_button)
        button_layout1.addSpacing(10)
        button_layout1.addWidget(self.auto_track_button)
        button_layout1.addSpacing(10)
        button_layout1.addWidget(self.test_network_button)
        
        button_layout2.addWidget(self.export_excel_button)
        button_layout2.addSpacing(10)
        button_layout2.addWidget(self.export_csv_button)
        button_layout2.addSpacing(10)
        button_layout2.addWidget(self.clear_button)
        button_layout2.addSpacing(10)
        button_layout2.addWidget(self.help_button)
        button_layout2.addSpacing(10)
        button_layout2.addWidget(self.night_mode_button)
        
        info_layout.addWidget(self.query_count_label)
        info_layout.addStretch()
        info_layout.addWidget(self.clear_logs_button)
        
        # 添加到主控制布局
        control_layout.addLayout(button_layout1)
        control_layout.addLayout(button_layout2)
        control_layout.addLayout(info_layout)
        
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
        
        # 更新站点下拉框的自动补全
        start_station_completer = QCompleter(stations)
        start_station_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.start_station.setCompleter(start_station_completer)
        
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
        
        # 更新站点下拉框的自动补全
        end_station_completer = QCompleter(stations)
        end_station_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.end_station.setCompleter(end_station_completer)
        
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
            # 记录查询开始时间
            query_start_time = time.time()
            
            self.update_status.emit("正在查询...")
            self.update_progress.emit(20)
            
            # 获取站点编码（使用缓存，避免重复查询）
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
            
            # 发送请求，使用最大重试次数
            try:
                response = client.get(url, params=params, max_retries=3)
                
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
                        # 进一步处理，确保字符串可以被正确编码
                        safe_content = repr(response_content).encode('utf-8', 'ignore').decode('utf-8')
                        logger.error(f"响应内容前200字符: {safe_content}")
                    except Exception as encode_error:
                        logger.error(f"记录响应内容时出现编码错误: {encode_error}")
                        # 尝试使用响应的原始字节来记录
                        try:
                            raw_content = response.content[:200]
                            safe_raw = repr(raw_content).encode('utf-8', 'ignore').decode('utf-8')
                            logger.error(f"响应原始字节前200: {safe_raw}")
                        except Exception as raw_error:
                            logger.error(f"记录原始响应内容时出现错误: {raw_error}")
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
                        
                        # 解析价格信息
                        prices = {}
                        # 注意：12306 API的价格信息格式可能会变化，这里使用更可靠的解析方式
                        # 尝试从不同位置获取价格信息
                        
                        # 调试：打印字段长度和部分字段值
                        logger.debug(f"字段长度: {len(fields)}")
                        if len(fields) > 45:
                            logger.debug(f"字段36-45: {fields[36:46]}")
                        
                        # 常见的价格字段位置（根据实际API返回调整）
                        # 注意：不同座位类型的价格字段位置可能不同
                        # 尝试从多个可能的位置获取价格信息
                        possible_price_positions = {
                            "硬座": [36, 42],
                            "硬卧": [37, 43],
                            "软卧": [38, 44],
                            "二等座": [39, 45],
                            "一等座": [40, 46],
                            "商务座": [41, 47]
                        }
                        
                        # 解析价格信息
                        for seat_type, positions in possible_price_positions.items():
                            for pos in positions:
                                if pos < len(fields):
                                    price = fields[pos]
                                    if price and price != "" and price != "0":
                                        # 尝试解析价格为数字
                                        try:
                                            # 提取数字部分
                                            import re
                                            clean_price = re.sub(r'[^0-9]', '', price)
                                            if clean_price:
                                                price_int = int(clean_price)
                                                # 检查价格是否合理（10-10000之间）
                                                if 10 <= price_int <= 10000:
                                                    prices[seat_type] = str(price_int)
                                                    break
                                        except:
                                            pass
                            if seat_type not in prices:
                                prices[seat_type] = "-"
                        
                        ticket_info = {
                            "train_number": train_number,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": duration,
                            "start_station": start_station_name,
                            "end_station": end_station_name,
                            "date": query_date,
                            "remaining_tickets": remaining_tickets,
                            "prices": prices
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
                
                # 计算查询用时
                end_time = time.time()
                query_time = end_time - query_start_time
                
                self.update_progress.emit(80)
                self.update_result.emit(tickets)
                
                # 显示查询用时
                logger.info(f"查询用时: {query_time:.2f} 秒")
                self.status_bar.showMessage(f"查询完成，用时: {query_time:.2f} 秒")
                self.update_status.emit(f"查询完成，找到 {len(tickets)} 条记录，用时: {query_time:.2f} 秒")
            except Exception as e:
                # 计算查询用时
                end_time = time.time()
                query_time = end_time - query_start_time
                
                logger.error(f"处理查询结果失败: {e}")
                logger.info(f"查询用时: {query_time:.2f} 秒")
                self.status_bar.showMessage(f"处理查询结果失败，用时: {query_time:.2f} 秒")
                self.update_status.emit(f"处理查询结果失败，用时: {query_time:.2f} 秒")
                self.update_result.emit([])
        except Exception as e:
            # 计算查询用时
            end_time = time.time()
            query_time = end_time - query_start_time
            
            logger.error(f"查询失败: {e}")
            logger.info(f"查询用时: {query_time:.2f} 秒")
            self.status_bar.showMessage(f"查询失败，用时: {query_time:.2f} 秒")
            self.update_status.emit(f"查询失败: {str(e)}，用时: {query_time:.2f} 秒")
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
            # 记录查询开始时间
            query_start_time = time.time()
            
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
                # 在主线程中显示结果
                QTimer.singleShot(0, lambda: self.display_transfer_results([]))
                return
            
            logger.info(f"准备在主线程中显示 {len(transfer_plans)} 个中转方案")
            
            # 保存中转方案到实例变量，以便在主线程中访问
            self.transfer_plans_to_display = transfer_plans
            
            # 计算查询用时
            end_time = time.time()
            query_time = end_time - query_start_time
            
            # 在主线程中显示结果
            from PyQt5.QtCore import QTimer
            
            logger.info("使用 QTimer.singleShot 在主线程中显示结果")
            try:
                # 使用 QTimer.singleShot 在主线程中执行
                QTimer.singleShot(0, self.display_transfer_results_in_main_thread)
                logger.info("QTimer.singleShot 调用完成")
            except Exception as e:
                logger.error(f"调用 QTimer.singleShot 失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 显示查询用时
            logger.info(f"查询用时: {query_time:.2f} 秒")
            self.status_bar.showMessage(f"查询完成，用时: {query_time:.2f} 秒")
            self.update_status.emit(f"查询完成，找到 {len(transfer_plans)} 个中转方案，用时: {query_time:.2f} 秒")
            self.update_progress.emit(100)
            
        except Exception as e:
            # 计算查询用时
            end_time = time.time()
            query_time = end_time - query_start_time
            
            logger.error(f"查询中转车次失败: {e}")
            logger.info(f"查询用时: {query_time:.2f} 秒")
            self.status_bar.showMessage(f"查询失败，用时: {query_time:.2f} 秒")
            self.update_status.emit(f"查询失败: {str(e)}，用时: {query_time:.2f} 秒")
            # 隐藏进度条
            QTimer.singleShot(0, lambda: self.progress_bar.setVisible(False))
        else:
            # 查询成功，在主线程中隐藏进度条
            QTimer.singleShot(0, lambda: self.progress_bar.setVisible(False))
    
    def display_results(self, tickets):
        """
        显示查询结果
        
        Args:
            tickets: 车票信息列表
        """
        from PyQt5.QtGui import QColor, QFont
        from PyQt5.QtWidgets import QTableWidgetItem, QTextEdit, QFrame
        
        try:
            # 保存结果
            self.query_results = tickets
            
            # 清空表格并释放控件
            self.clear_table_widgets()
            self.result_table.setRowCount(0)
            logger.info("表格已清空")
            
            # 计算总行数（包含标题行）
            total_rows = 1 + len(tickets) if tickets else 0
            logger.info(f"总共有 {total_rows} 行数据需要显示")
            
            # 预设置表格行数，避免频繁的行插入操作
            self.result_table.setRowCount(total_rows)
            logger.info("表格行数已设置")
            
            if tickets:
                # 添加直达车次标题行
                logger.info("添加直达车次标题行")
                
                # 设置标题行的样式
                title_font = QFont()
                title_font.setBold(True)
                title_font.setPointSize(10)
                
                # 创建标题单元格
                title_item = QTableWidgetItem("直达车次")
                title_item.setFont(title_font)
                title_item.setBackground(QColor(200, 220, 255))  # 浅蓝色背景
                title_item.setTextAlignment(132)  # 居中对齐
                
                # 设置标题行的单元格
                self.result_table.setItem(0, 0, title_item)
                
                # 设置车次数量
                count_item = QTableWidgetItem(f"共 {len(tickets)} 个车次")
                count_item.setFont(title_font)
                count_item.setBackground(QColor(200, 220, 255))
                count_item.setTextAlignment(132)
                self.result_table.setItem(0, 3, count_item)
                
                # 填充表格
                for idx, ticket in enumerate(tickets):
                    row_position = idx + 1  # 跳过标题行
                    logger.info(f"处理第 {idx+1} 个直达车次: {ticket['train_number']}")
                    
                    # 为不同车次设置交替背景颜色
                    bg_color = QColor(245, 245, 245) if idx % 2 == 0 else QColor(255, 255, 255)
                    
                    # 填充数据
                    train_number_item = QTableWidgetItem(ticket["train_number"])
                    train_number_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 0, train_number_item)
                    
                    start_time_item = QTableWidgetItem(ticket["start_time"])
                    start_time_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 1, start_time_item)
                    
                    end_time_item = QTableWidgetItem(ticket["end_time"])
                    end_time_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 2, end_time_item)
                    
                    duration_item = QTableWidgetItem(ticket["duration"])
                    duration_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 3, duration_item)
                    
                    start_station_item = QTableWidgetItem(ticket["start_station"])
                    start_station_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 4, start_station_item)
                    
                    end_station_item = QTableWidgetItem(ticket["end_station"])
                    end_station_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 5, end_station_item)
                    
                    date_item = QTableWidgetItem(ticket["date"])
                    date_item.setBackground(bg_color)
                    self.result_table.setItem(row_position, 6, date_item)
                    
                    # 格式化余票信息，突出显示有票的座位
                    remaining_lines = []
                    for k, v in ticket["remaining_tickets"].items():
                        if v:
                            # 获取对应座位的价格
                            price = ticket.get("prices", {}).get(k, "-")
                            price_str = f" (¥{price})" if price != "-" else ""
                            
                            if v == "有":
                                # 使用更显眼的样式突出显示有票的座位
                                line = f"<span style='font-weight: bold; font-size: 20px; color: green;'>{k}: {v}{price_str}</span>"
                            elif v != "无":
                                # 显示有具体数量的余票
                                line = f"<span style='font-weight: bold; font-size: 20px; color: blue;'>{k}: {v}{price_str}</span>"
                            else:
                                # 无票信息使用灰色，不突出显示
                                line = f"<span style='font-size: 20px; color: gray;'>{k}: {v}{price_str}</span>"
                            remaining_lines.append(line)
                    remaining_info = "<br>" + "<br>".join(remaining_lines)
                    # 创建文本编辑框作为单元格widget，支持HTML
                    text_edit = QTextEdit()
                    text_edit.setHtml(remaining_info)
                    text_edit.setReadOnly(True)
                    text_edit.setFrameShape(QFrame.NoFrame)
                    text_edit.setStyleSheet(f"background-color: {bg_color.name()}; border: none;")
                    # 设置文本编辑框的大小
                    text_edit.setMinimumHeight(100)
                    text_edit.setMaximumHeight(200)
                    # 将文本编辑框设置为单元格widget
                    self.result_table.setCellWidget(row_position, 7, text_edit)
            
            # 启用导出按钮
            self.export_excel_button.setEnabled(len(tickets) > 0)
            self.export_csv_button.setEnabled(len(tickets) > 0)
            logger.info(f"导出按钮状态已更新，Excel: {self.export_excel_button.isEnabled()}, CSV: {self.export_csv_button.isEnabled()}")
            
            # 调整列宽
            self.result_table.resizeColumnsToContents()
            logger.info("直达车次结果显示完成")
        except Exception as e:
            logger.error(f"显示直达车次结果失败: {e}")
            import traceback
            traceback.print_exc()
    
    def display_transfer_results_in_main_thread(self):
        """
        在主线程中显示中转车次结果
        这个方法会被 QMetaObject.invokeMethod 调用
        """
        try:
            logger.info("开始在主线程中显示中转车次结果")
            if hasattr(self, 'transfer_plans_to_display'):
                transfer_plans = self.transfer_plans_to_display
                logger.info(f"从实例变量中获取到 {len(transfer_plans)} 个中转方案")
                self.display_transfer_results(transfer_plans)
                logger.info("中转车次结果显示完成")
            else:
                logger.error("没有找到 transfer_plans_to_display 实例变量")
        except Exception as e:
            logger.error(f"在主线程中显示中转车次结果失败: {e}")
            import traceback
            traceback.print_exc()
    
    def display_transfer_results(self, transfer_plans):
        """
        显示中转车次结果
        
        Args:
            transfer_plans: 中转车次计划列表
        """
        from PyQt5.QtGui import QColor, QFont
        from PyQt5.QtWidgets import QTableWidgetItem, QTextEdit, QFrame, QApplication
        
        try:
            # 限制显示的中转方案数量，避免处理过多数据
            max_plans = 100
            if len(transfer_plans) > max_plans:
                logger.info(f"中转方案数量过多，只显示前 {max_plans} 个方案")
                transfer_plans = transfer_plans[:max_plans]
            
            logger.info(f"开始显示中转车次结果，共 {len(transfer_plans)} 个方案")
            
            # 保存结果
            self.query_results = transfer_plans
            
            # 清空表格并释放控件
            self.clear_table_widgets()
            self.result_table.setRowCount(0)
            logger.info("表格已清空")
            
            # 计算总行数（每个方案包含标题行 + 车次行）
            total_rows = sum(1 + len(plan['transfers']) for plan in transfer_plans)
            logger.info(f"总共有 {total_rows} 行数据需要显示")
            
            # 预设置表格行数，避免频繁的行插入操作
            self.result_table.setRowCount(total_rows)
            logger.info("表格行数已设置")
            
            # 填充表格
            current_row = 0
            for plan_idx, plan in enumerate(transfer_plans):
                logger.info(f"处理第 {plan_idx+1} 个中转方案，包含 {len(plan['transfers'])} 个车次")
                
                # 添加方案标题行
                logger.info(f"添加第 {plan_idx+1} 个方案的标题行")
                
                # 设置标题行的样式
                title_font = QFont()
                title_font.setBold(True)
                title_font.setPointSize(10)
                
                # 创建标题单元格
                title_item = QTableWidgetItem(f"中转方案 {plan_idx+1}")
                title_item.setFont(title_font)
                title_item.setBackground(QColor(200, 220, 255))  # 浅蓝色背景
                title_item.setTextAlignment(132)  # 居中对齐
                
                # 设置标题行的单元格
                self.result_table.setItem(current_row, 0, title_item)
                
                # 设置总历时
                total_duration_item = QTableWidgetItem(f"总历时: {plan.get('total_duration', '未知')}")
                total_duration_item.setFont(title_font)
                total_duration_item.setBackground(QColor(200, 220, 255))
                total_duration_item.setTextAlignment(132)
                self.result_table.setItem(current_row, 3, total_duration_item)
                
                # 设置中转站信息
                transfer_station_item = QTableWidgetItem(f"中转站: {plan.get('transfer_station', '未知')}")
                transfer_station_item.setFont(title_font)
                transfer_station_item.setBackground(QColor(200, 220, 255))
                transfer_station_item.setTextAlignment(132)
                self.result_table.setItem(current_row, 4, transfer_station_item)
                
                # 设置中转时间
                transfer_time_item = QTableWidgetItem(f"中转时间: {plan.get('transfer_time', '未知')}")
                transfer_time_item.setFont(title_font)
                transfer_time_item.setBackground(QColor(200, 220, 255))
                transfer_time_item.setTextAlignment(132)
                self.result_table.setItem(current_row, 5, transfer_time_item)
                
                # 合并标题行的单元格（如果需要）
                # 注意：QTableWidget的合并单元格功能有限，这里我们只是设置了每个单元格的样式
                
                # 增加当前行索引
                current_row += 1
                
                # 为每个中转方案的车次设置背景颜色
                plan_background_color = QColor(245, 245, 245) if plan_idx % 2 == 0 else QColor(255, 255, 255)
                
                # 为每个中转方案创建多行
                for i, transfer in enumerate(plan["transfers"]):
                    logger.info(f"处理第 {current_row} 行，车次: {transfer['train_number']}")
                    
                    # 填充数据
                    train_number_item = QTableWidgetItem(transfer["train_number"])
                    train_number_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 0, train_number_item)
                    
                    start_time_item = QTableWidgetItem(transfer["start_time"])
                    start_time_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 1, start_time_item)
                    
                    end_time_item = QTableWidgetItem(transfer["end_time"])
                    end_time_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 2, end_time_item)
                    
                    duration_item = QTableWidgetItem(transfer["duration"])
                    duration_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 3, duration_item)
                    
                    start_station_item = QTableWidgetItem(transfer["start_station"])
                    start_station_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 4, start_station_item)
                    
                    end_station_item = QTableWidgetItem(transfer["end_station"])
                    end_station_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 5, end_station_item)
                    
                    date_item = QTableWidgetItem(plan["date"])
                    date_item.setBackground(plan_background_color)
                    self.result_table.setItem(current_row, 6, date_item)
                    
                    # 格式化余票信息，突出显示有票的座位
                    remaining_lines = []
                    for k, v in transfer["remaining_tickets"].items():
                        if v:
                            # 获取对应座位的价格
                            price = transfer.get("prices", {}).get(k, "-")
                            price_str = f" (¥{price})" if price != "-" else ""
                            
                            if v == "有":
                                # 使用更显眼的样式突出显示有票的座位
                                line = f"<span style='font-weight: bold; font-size: 20px; color: green;'>{k}: {v}{price_str}</span>"
                            elif v != "无":
                                # 显示有具体数量的余票
                                line = f"<span style='font-weight: bold; font-size: 20px; color: blue;'>{k}: {v}{price_str}</span>"
                            else:
                                # 无票信息使用灰色，不突出显示
                                line = f"<span style='font-size: 20px; color: gray;'>{k}: {v}{price_str}</span>"
                            remaining_lines.append(line)
                    remaining_info = "<br>" + "<br>".join(remaining_lines)
                    # 创建文本编辑框作为单元格widget，支持HTML
                    text_edit = QTextEdit()
                    text_edit.setHtml(remaining_info)
                    text_edit.setReadOnly(True)
                    text_edit.setFrameShape(QFrame.NoFrame)
                    text_edit.setStyleSheet(f"background-color: {plan_background_color.name()}; border: none;")
                    # 设置文本编辑框的大小
                    text_edit.setMinimumHeight(100)
                    text_edit.setMaximumHeight(200)
                    # 将文本编辑框设置为单元格widget
                    self.result_table.setCellWidget(current_row, 7, text_edit)
                    
                    # 增加当前行索引
                    current_row += 1
                    
                    # 每处理10个中转方案后，处理事件队列，避免UI卡顿
                    if (plan_idx + 1) % 10 == 0:
                        QApplication.processEvents()
            
            # 启用导出按钮
            self.export_excel_button.setEnabled(len(transfer_plans) > 0)
            self.export_csv_button.setEnabled(len(transfer_plans) > 0)
            
            # 调整列宽
            self.result_table.resizeColumnsToContents()
            logger.info(f"导出按钮状态已更新，Excel: {self.export_excel_button.isEnabled()}, CSV: {self.export_csv_button.isEnabled()}")
            logger.info("中转车次结果显示完成")
        except Exception as e:
            logger.error(f"显示中转车次结果失败: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    def clear_table_widgets(self):
        """
        清空表格中的所有控件，释放内存
        """
        try:
            # 遍历所有行和列，删除单元格中的控件
            for row in range(self.result_table.rowCount()):
                for col in range(self.result_table.columnCount()):
                    # 检查是否有控件
                    widget = self.result_table.cellWidget(row, col)
                    if widget:
                        # 移除控件
                        self.result_table.setCellWidget(row, col, None)
                        # 显式删除控件
                        widget.deleteLater()
            logger.info("表格控件已清空")
        except Exception as e:
            logger.error(f"清空表格控件失败: {e}")
    
    def clear_results(self):
        """
        清空结果
        """
        self.clear_table_widgets()
        self.result_table.setRowCount(0)
        self.query_results = []
        self.export_excel_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        self.update_status.emit("结果已清空")
    
    def show_auto_track_dialog(self):
        """
        显示自动盯票配置对话框
        """
        # 显示盯票功能说明
        track_info = """
盯票功能说明：
1. 只能盯直达票，中转票不支持
2. 自动查询间隔不能低于30秒
3. 请合理设置查询间隔，避免对12306服务器造成负担
4. 如启用邮箱提醒，请确保邮箱地址和授权码正确
        """
        QMessageBox.information(self, "盯票功能说明", track_info)
        
        # 获取当前查询参数
        start_station = self.start_station.currentText().strip()
        end_station = self.end_station.currentText().strip()
        query_date = self.query_date.date().toString("yyyy-MM-dd")
        
        # 验证参数
        if not start_station or not end_station:
            QMessageBox.warning(self, "警告", "请先选择出发地和目的地")
            return
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("自动盯票配置")
        dialog.setMinimumWidth(400)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        # 显示出发地和目的地
        basic_layout.addRow("出发地:", QLabel(start_station))
        basic_layout.addRow("目的地:", QLabel(end_station))
        basic_layout.addRow("查询日期:", QLabel(query_date))
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 创建车类型选择组
        train_type_group = QGroupBox("选择车类型（可多选）")
        train_type_layout = QVBoxLayout()
        
        # 车类型选项
        train_types = ["全部", "高铁", "动车", "普通列车"]
        self.train_type_checkboxes = {}
        
        for train_type in train_types:
            checkbox = QCheckBox(train_type)
            if train_type in self.auto_track_config['train_types']:
                checkbox.setChecked(True)
            train_type_layout.addWidget(checkbox)
            self.train_type_checkboxes[train_type] = checkbox
        
        train_type_group.setLayout(train_type_layout)
        layout.addWidget(train_type_group)
        
        # 创建座位等级选择组
        seat_class_group = QGroupBox("选择座位等级（可多选）")
        seat_class_layout = QVBoxLayout()
        
        # 座位等级选项
        seat_classes = ["商务座", "一等座", "二等座", "硬卧", "硬座", "软卧", "站票"]
        self.seat_class_checkboxes = {}
        
        for seat_class in seat_classes:
            checkbox = QCheckBox(seat_class)
            if seat_class in self.auto_track_config['seat_classes']:
                checkbox.setChecked(True)
            seat_class_layout.addWidget(checkbox)
            self.seat_class_checkboxes[seat_class] = checkbox
        
        seat_class_group.setLayout(seat_class_layout)
        layout.addWidget(seat_class_group)
        
        # 创建车次选择组
        train_group = QGroupBox("选择车次（可多选）")
        train_layout = QVBoxLayout()
        
        # 创建车次搜索和筛选区域
        search_filter_layout = QHBoxLayout()
        
        # 车次搜索框
        self.train_search_edit = QLineEdit()
        self.train_search_edit.setPlaceholderText("输入车次编号关键词搜索")
        self.train_search_edit.textChanged.connect(self.filter_trains)
        search_filter_layout.addWidget(self.train_search_edit)
        
        # 车次类型筛选下拉框
        self.train_type_filter = QComboBox()
        self.train_type_filter.addItem("全部类型")
        self.train_type_filter.addItem("G字头")
        self.train_type_filter.addItem("D字头")
        self.train_type_filter.addItem("C字头")
        self.train_type_filter.addItem("Z字头")
        self.train_type_filter.addItem("T字头")
        self.train_type_filter.addItem("K字头")
        self.train_type_filter.addItem("其他类型")
        self.train_type_filter.currentTextChanged.connect(self.filter_trains)
        search_filter_layout.addWidget(self.train_type_filter)
        
        # 加载车次按钮
        self.load_trains_button = QPushButton("加载车次")
        self.load_trains_button.clicked.connect(lambda: self.load_trains(start_station, end_station, query_date))
        search_filter_layout.addWidget(self.load_trains_button)
        
        train_layout.addLayout(search_filter_layout)
        
        # 创建车次列表表格
        self.train_table = QTableWidget()
        self.train_table.setColumnCount(7)
        self.train_table.setHorizontalHeaderLabels([
            "选择", "车次", "出发站", "到达站", "发车时间", "到达时间", "历时"
        ])
        # 设置第一列为复选框
        self.train_table.setColumnWidth(0, 50)
        # 设置其他列宽
        self.train_table.setColumnWidth(1, 80)
        self.train_table.setColumnWidth(2, 100)
        self.train_table.setColumnWidth(3, 100)
        self.train_table.setColumnWidth(4, 80)
        self.train_table.setColumnWidth(5, 80)
        self.train_table.setColumnWidth(6, 80)
        # 设置表格自动调整行高
        self.train_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        train_layout.addWidget(self.train_table)
        
        # 创建加载状态标签
        self.train_load_status = QLabel("请点击'加载车次'按钮获取当日车次")
        self.train_load_status.setAlignment(Qt.AlignCenter)
        train_layout.addWidget(self.train_load_status)
        
        train_group.setLayout(train_layout)
        layout.addWidget(train_group)
        
        # 创建时间间隔设置组
        interval_group = QGroupBox("查询间隔设置")
        interval_layout = QHBoxLayout()
        
        min_interval_label = QLabel("最小间隔（秒）:")
        self.min_interval_spinbox = QSpinBox()
        self.min_interval_spinbox.setMinimum(30)  # 自动查询间隔不能低于30秒
        self.min_interval_spinbox.setMaximum(300)
        self.min_interval_spinbox.setValue(max(self.auto_track_config.get('min_interval', 30), 30))  # 确保当前值不低于30秒
        
        max_interval_label = QLabel("最大间隔（秒）:")
        self.max_interval_spinbox = QSpinBox()
        self.max_interval_spinbox.setMinimum(30)  # 自动查询间隔不能低于30秒
        self.max_interval_spinbox.setMaximum(300)
        self.max_interval_spinbox.setValue(max(self.auto_track_config.get('max_interval', 60), 30))  # 确保当前值不低于30秒
        
        interval_layout.addWidget(min_interval_label)
        interval_layout.addWidget(self.min_interval_spinbox)
        interval_layout.addSpacing(20)
        interval_layout.addWidget(max_interval_label)
        interval_layout.addWidget(self.max_interval_spinbox)
        interval_layout.addStretch()
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # 创建邮箱提醒设置组
        email_group = QGroupBox("邮箱提醒设置")
        email_layout = QFormLayout()
        
        # 邮箱提醒启用复选框
        self.email_alert_checkbox = QCheckBox("启用邮箱提醒")
        self.email_alert_checkbox.setChecked(self.auto_track_config.get('email_alert', False))
        # 连接信号槽，当复选框状态改变时，控制其他控件的启用/禁用状态
        self.email_alert_checkbox.stateChanged.connect(self.toggle_email_fields)
        email_layout.addRow(self.email_alert_checkbox)
        
        # 邮箱地址输入框
        self.email_address_edit = QLineEdit()
        self.email_address_edit.setPlaceholderText("请输入邮箱地址")
        self.email_address_edit.setText(self.auto_track_config.get('email_address', ''))
        email_layout.addRow("邮箱地址:", self.email_address_edit)
        
        # 邮箱授权码输入框
        self.email_password_edit = QLineEdit()
        self.email_password_edit.setPlaceholderText("请输入邮箱授权码")
        self.email_password_edit.setEchoMode(QLineEdit.Password)
        self.email_password_edit.setText(self.auto_track_config.get('email_password', ''))
        email_layout.addRow("邮箱授权码:", self.email_password_edit)
        
        # 记住邮箱配置复选框
        self.remember_email_checkbox = QCheckBox("记住邮箱配置")
        self.remember_email_checkbox.setChecked(self.auto_track_config.get('remember_email', False))
        email_layout.addRow(self.remember_email_checkbox)
        
        # 初始状态下，根据邮箱提醒是否启用，设置其他控件的启用状态
        self.toggle_email_fields(self.email_alert_checkbox.checkState())
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        # 创建按钮组
        button_layout = QHBoxLayout()
        
        self.start_track_button = QPushButton("开始盯票")
        self.stop_track_button = QPushButton("停止盯票")
        
        # 根据当前状态设置按钮状态和配置控件状态
        if self.auto_track_running:
            self.start_track_button.setEnabled(False)
            self.stop_track_button.setEnabled(True)
            # 禁用所有配置控件
            self.disable_config_controls()
        else:
            self.start_track_button.setEnabled(True)
            self.stop_track_button.setEnabled(False)
        
        self.start_track_button.clicked.connect(lambda: self.start_auto_track(dialog, start_station, end_station, query_date))
        self.stop_track_button.clicked.connect(self.stop_auto_track)
        
        button_layout.addWidget(self.start_track_button)
        button_layout.addWidget(self.stop_track_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def load_trains(self, start_station, end_station, query_date):
        """
        加载查询日当日的实际运行车次
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
        """
        # 显示加载状态
        self.train_load_status.setText("正在加载车次数据...")
        self.train_load_status.setStyleSheet("color: blue;")
        self.load_trains_button.setEnabled(False)
        
        # 记录开始加载的时间
        self.load_trains_start_time = time.time()
        
        # 设置超时定时器（20秒）
        self.load_trains_timer = QTimer()
        self.load_trains_timer.setSingleShot(True)
        self.load_trains_timer.timeout.connect(self.check_load_trains_timeout)
        self.load_trains_timer.start(20000)  # 20秒超时
        
        # 在新线程中加载车次数据
        thread = threading.Thread(
            target=self._load_trains_thread,
            args=(start_station, end_station, query_date)
        )
        thread.daemon = True
        thread.start()
    
    def check_load_trains_timeout(self):
        """
        检查加载车次是否超时
        """
        # 检查是否已经超时
        elapsed = time.time() - self.load_trains_start_time
        if elapsed >= 20:
            # 显示超时错误
            error_msg = "加载车次数据超时，请检查网络连接后重试"
            self.train_load_status.setText(f"加载失败: {error_msg}")
            self.train_load_status.setStyleSheet("color: red;")
            self.load_trains_button.setEnabled(True)
            QMessageBox.warning(self, "警告", error_msg)
    
    def cancel_load_trains_timer(self):
        """
        取消加载车次的超时定时器
        """
        if hasattr(self, 'load_trains_timer') and self.load_trains_timer.isActive():
            self.load_trains_timer.stop()
    
    def event(self, event):
        """
        处理自定义事件
        """
        if event.type() == QEvent.User:
            if isinstance(event, UpdateTrainTableEvent):
                logger.info("收到更新车次表格事件，车次数量: {}".format(len(event.trains)))
                self.update_train_table(event.trains)
                return True
            elif hasattr(event, 'message'):
                # 处理通知事件
                logger.info("收到通知事件，显示余票通知")
                self.show_ticket_notification(event.message)
                return True
            else:
                # 处理状态更新事件
                logger.info("收到状态更新事件，更新自动盯票状态")
                self.update_auto_track_status()
                return True
        return super().event(event)
    
    def _load_trains_thread(self, start_station, end_station, query_date):
        """
        加载车次数据的线程函数
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
        """
        try:
            # 获取站点编码
            from_station = client.get_station_code(start_station)
            to_station = client.get_station_code(end_station)
            
            # 检查站点编码是否有效
            if from_station == start_station or to_station == end_station:
                error_msg = f"站点编码无效: {start_station} -> {end_station}"
                logger.error(error_msg)
                QTimer.singleShot(0, lambda: self.show_train_load_error(error_msg))
                return
            
            # 构建查询参数
            url = "https://kyfw.12306.cn/otn/leftTicket/query"
            params = {
                "leftTicketDTO.train_date": query_date,
                "leftTicketDTO.from_station": from_station,
                "leftTicketDTO.to_station": to_station,
                "purpose_codes": "ADULT"
            }
            
            # 发送请求
            response = client.get(url, params=params, max_retries=3)
            result = response.json()
            
            # 处理查询结果
            if result.get("status"):
                data = result.get("data", {})
                result_list = data.get("result", [])
                
                logger.info(f"查询结果包含 {len(result_list)} 个车次")
                
                trains = []
                for item in result_list:
                    fields = item.split("|")
                    if len(fields) < 30:
                        continue
                    
                    train_number = fields[3]
                    start_station_code = fields[6]
                    end_station_code = fields[7]
                    start_station_name = client.get_station_name(start_station_code)
                    end_station_name = client.get_station_name(end_station_code)
                    start_time = fields[8]
                    end_time = fields[9]
                    duration = fields[10]
                    
                    # 获取车次类型
                    train_type = "其他类型"
                    if train_number.startswith("G"):
                        train_type = "G字头"
                    elif train_number.startswith("D"):
                        train_type = "D字头"
                    elif train_number.startswith("C"):
                        train_type = "C字头"
                    elif train_number.startswith("Z"):
                        train_type = "Z字头"
                    elif train_number.startswith("T"):
                        train_type = "T字头"
                    elif train_number.startswith("K"):
                        train_type = "K字头"
                    
                    trains.append({
                        "train_number": train_number,
                        "start_station": start_station_name,
                        "end_station": end_station_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "train_type": train_type
                    })
                
                # 保存车次数据
                self.all_trains = trains
                
                logger.info(f"成功解析 {len(trains)} 个车次")
                
                # 在主线程中更新表格
                logger.info("准备更新UI，车次数量: {}".format(len(trains)))
                # 使用QApplication.postEvent发送事件，在主线程中更新UI
                event = UpdateTrainTableEvent(trains)
                QApplication.postEvent(self, event)
                logger.info("事件已发送到事件队列")
            else:
                error_msg = f"查询失败: {result.get('messages', '未知错误')}"
                logger.error(error_msg)
                QTimer.singleShot(0, lambda: self.show_train_load_error(error_msg))
        except Exception as e:
            error_msg = f"加载车次数据失败: {str(e)}"
            logger.error(error_msg)
            QTimer.singleShot(0, lambda: self.show_train_load_error(error_msg))
        finally:
            # 确保无论是否发生异常，加载按钮都会重新启用
            QTimer.singleShot(0, lambda: self.load_trains_button.setEnabled(True))
    
    def update_train_table(self, trains):
        """
        更新车次表格
        
        Args:
            trains: 车次数据列表
        """
        # 取消超时定时器
        self.cancel_load_trains_timer()
        
        # 清空表格
        self.train_table.setRowCount(0)
        
        # 填充表格
        for train in trains:
            row_position = self.train_table.rowCount()
            self.train_table.insertRow(row_position)
            
            # 添加复选框
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.Unchecked)
            # 检查是否在之前的选择中
            if train['train_number'] in self.auto_track_config.get('selected_trains', []):
                checkbox.setCheckState(Qt.Checked)
            self.train_table.setItem(row_position, 0, checkbox)
            
            # 填充其他数据
            self.train_table.setItem(row_position, 1, QTableWidgetItem(train['train_number']))
            self.train_table.setItem(row_position, 2, QTableWidgetItem(train['start_station']))
            self.train_table.setItem(row_position, 3, QTableWidgetItem(train['end_station']))
            self.train_table.setItem(row_position, 4, QTableWidgetItem(train['start_time']))
            self.train_table.setItem(row_position, 5, QTableWidgetItem(train['end_time']))
            self.train_table.setItem(row_position, 6, QTableWidgetItem(train['duration']))
        
        # 更新加载状态
        self.train_load_status.setText(f"成功加载 {len(trains)} 个车次")
        self.train_load_status.setStyleSheet("color: green;")
        self.load_trains_button.setEnabled(True)
    
    def show_train_load_error(self, error_msg):
        """
        显示车次加载错误
        
        Args:
            error_msg: 错误信息
        """
        # 取消超时定时器
        self.cancel_load_trains_timer()
        
        self.train_load_status.setText(f"加载失败: {error_msg}")
        self.train_load_status.setStyleSheet("color: red;")
        self.load_trains_button.setEnabled(True)
        QMessageBox.warning(self, "警告", error_msg)
    
    def filter_trains(self):
        """
        筛选车次
        """
        search_text = self.train_search_edit.text().strip()
        filter_type = self.train_type_filter.currentText()
        
        # 筛选车次
        filtered_trains = []
        for train in self.all_trains:
            # 按搜索文本筛选
            if search_text and search_text not in train['train_number']:
                continue
            
            # 按车次类型筛选
            if filter_type != "全部类型" and train['train_type'] != filter_type:
                continue
            
            filtered_trains.append(train)
        
        # 更新表格
        self.update_train_table(filtered_trains)
    
    def start_auto_track(self, dialog, start_station, end_station, query_date):
        """
        开始自动盯票
        
        Args:
            dialog: 配置对话框
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
        """
        # 获取选中的车类型
        selected_train_types = []
        for train_type, checkbox in self.train_type_checkboxes.items():
            if checkbox.isChecked():
                selected_train_types.append(train_type)
        
        # 获取选中的座位等级
        selected_seat_classes = []
        for seat_class, checkbox in self.seat_class_checkboxes.items():
            if checkbox.isChecked():
                selected_seat_classes.append(seat_class)
        
        # 获取选中的车次
        selected_trains = []
        if hasattr(self, 'train_table'):
            for row in range(self.train_table.rowCount()):
                checkbox_item = self.train_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    train_number_item = self.train_table.item(row, 1)
                    if train_number_item:
                        selected_trains.append(train_number_item.text())
        
        # 获取查询间隔范围
        min_interval = self.min_interval_spinbox.value()
        max_interval = self.max_interval_spinbox.value()
        
        # 确保最小间隔不低于30秒，防止恶意攻击12306服务器
        min_interval = max(min_interval, 30)
        max_interval = max(max_interval, min_interval)  # 确保最大间隔不小于最小间隔
        
        # 验证选择
        if not selected_train_types:
            QMessageBox.warning(self, "警告", "请至少选择一种车类型")
            return
        
        if not selected_seat_classes:
            QMessageBox.warning(self, "警告", "请至少选择一种座位等级")
            return
        
        if not selected_trains:
            QMessageBox.warning(self, "警告", "请至少选择一种车次")
            return
        
        if selected_trains:
            logger.info(f"用户选择了以下车次进行盯票: {', '.join(selected_trains)}")
        
        # 获取邮箱配置
        email_alert = self.email_alert_checkbox.isChecked()
        email_address = self.email_address_edit.text().strip()
        email_password = self.email_password_edit.text().strip()
        remember_email = self.remember_email_checkbox.isChecked()
        
        # 验证邮箱配置
        if email_alert:
            if not email_address:
                QMessageBox.warning(self, "警告", "请输入邮箱地址")
                return
            if not email_password:
                QMessageBox.warning(self, "警告", "请输入邮箱授权码")
                return
        
        # 更新配置
        self.auto_track_config = {
            'train_types': selected_train_types,
            'seat_classes': selected_seat_classes,
            'min_interval': min_interval,
            'max_interval': max_interval,
            'start_station': start_station,
            'end_station': end_station,
            'query_date': query_date,
            'selected_trains': selected_trains,
            'email_alert': email_alert,
            'email_address': email_address if remember_email else '',
            'email_password': email_password if remember_email else '',
            'remember_email': remember_email
        }
        
        # 配置会在程序退出时自动保存到 settings.json 文件中
        
        # 禁用所有配置控件
        self.disable_config_controls()
        
        # 重置查询计数器
        self.query_count = 0
        
        # 使用信号触发查询次数更新
        self.update_query_count_signal.emit(self.query_count)
        
        # 启动盯票线程
        self.auto_track_running = True
        self.auto_track_thread = threading.Thread(
            target=self.auto_track_task,
            args=(start_station, end_station, query_date, selected_train_types, selected_seat_classes, min_interval, max_interval, selected_trains, email_alert, email_address, email_password)
        )
        self.auto_track_thread.daemon = True
        self.auto_track_thread.start()
        
        # 更新状态
        self.update_auto_track_status()
        
        # 显示提示
        message = f"自动盯票已启动\n查询间隔: {min_interval}-{max_interval}秒（随机）\n监控车类型: {', '.join(selected_train_types)}\n监控座位等级: {', '.join(selected_seat_classes)}"
        if selected_trains:
            message += f"\n监控车次: {', '.join(selected_trains)}"
        else:
            message += "\n监控车次: 全部车次"
        QMessageBox.information(self, "提示", message)
        
        # 关闭对话框
        dialog.accept()
    
    def stop_auto_track(self):
        """
        停止自动盯票
        """
        self.auto_track_running = False
        if self.auto_track_thread:
            self.auto_track_thread.join(timeout=5)
        
        # 启用所有配置控件
        if hasattr(self, 'enable_config_controls'):
            self.enable_config_controls()
        
        # 更新状态
        self.update_auto_track_status()
        
        # 显示提示
        QMessageBox.information(self, "提示", "自动盯票已停止")
        self.update_status.emit("自动盯票已停止")
    
    def update_auto_track_status(self):
        """
        更新自动盯票状态
        """
        logger.info(f"更新自动盯票状态，当前状态: {'运行中' if self.auto_track_running else '未启动'}")
        
        # 更新按钮状态
        if hasattr(self, 'start_track_button'):
            self.start_track_button.setEnabled(not self.auto_track_running)
        if hasattr(self, 'stop_track_button'):
            self.stop_track_button.setEnabled(self.auto_track_running)
        
        # 更新自动盯票按钮文本
        if hasattr(self, 'auto_track_button'):
            if self.auto_track_running:
                self.auto_track_button.setText("停止盯票")
            else:
                self.auto_track_button.setText("自动盯票")
        else:
            logger.error("auto_track_button 不存在")
        
        # 更新自动盯票状态标签
        if hasattr(self, 'auto_track_status_label'):
            if self.auto_track_running:
                min_interval = self.auto_track_config.get('min_interval', 30)
                max_interval = self.auto_track_config.get('max_interval', 60)
                self.auto_track_status_label.setText(f"自动盯票: 运行中 ({min_interval}-{max_interval}秒随机)")
                self.auto_track_status_label.setStyleSheet("color: green;")
            else:
                self.auto_track_status_label.setText("自动盯票: 未启动")
                self.auto_track_status_label.setStyleSheet("color: gray;")
        else:
            logger.error("auto_track_status_label 不存在")
    
    def auto_track_task(self, start_station, end_station, query_date, train_types, seat_classes, min_interval, max_interval, selected_trains, email_alert, email_address, email_password):
        """
        自动盯票任务
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
            train_types: 车类型列表
            seat_classes: 座位等级列表
            min_interval: 最小查询间隔（秒）
            max_interval: 最大查询间隔（秒）
            selected_trains: 选中的车次列表
            email_alert: 是否启用邮箱提醒
            email_address: 邮箱地址
            email_password: 邮箱授权码
        """
        import smtplib
        import random
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.header import Header
        
        def send_email_notification(message):
            """
            发送邮件通知
            
            Args:
                message: 通知消息
            """
            if not email_alert or not email_address or not email_password:
                return
            
            server = None
            try:
                # 邮件服务器配置
                smtp_server = "smtp.qq.com"  # 默认使用QQ邮箱服务器
                smtp_port = 587
                
                # 根据邮箱地址自动选择邮件服务器
                if "@163.com" in email_address:
                    smtp_server = "smtp.163.com"
                elif "@126.com" in email_address:
                    smtp_server = "smtp.126.com"
                elif "@gmail.com" in email_address:
                    smtp_server = "smtp.gmail.com"
                elif "@outlook.com" in email_address or "@hotmail.com" in email_address:
                    smtp_server = "smtp.office365.com"
                
                # 创建邮件
                msg = MIMEMultipart()
                msg['From'] = email_address
                msg['To'] = email_address
                msg['Subject'] = Header("余票通知", 'utf-8')
                
                # 邮件正文
                body = f"<html><body><p>{message.replace('\n', '<br>')}</p></body></html>"
                msg.attach(MIMEText(body, 'html', 'utf-8'))
                
                # 发送邮件
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(email_address, email_password)
                server.send_message(msg)
                logger.info("邮件通知发送成功")
            except Exception as e:
                logger.error(f"发送邮件通知失败: {e}")
            finally:
                # 确保服务器连接被关闭
                if server:
                    try:
                        server.quit()
                    except:
                        pass
        logger.info(f"自动盯票任务已启动: {start_station} -> {end_station}, {query_date}")
        self.update_status.emit(f"自动盯票已启动: {start_station} -> {end_station}")
        
        while self.auto_track_running:
            try:
                # 增加查询计数
                self.query_count += 1
                current_count = self.query_count
                logger.info(f"执行第 {current_count} 次自动查询")
                
                # 使用信号触发查询次数更新
                self.update_query_count_signal.emit(current_count)
                
                # 获取站点编码
                from_station = client.get_station_code(start_station)
                to_station = client.get_station_code(end_station)
                
                # 检查站点编码是否有效
                if from_station == start_station or to_station == end_station:
                    logger.error(f"站点编码无效: {start_station} -> {end_station}")
                    # 随机选择等待时间
                    random_interval = random.randint(min_interval, max_interval)
                    time.sleep(random_interval)
                    continue
                
                # 构建查询参数
                url = "https://kyfw.12306.cn/otn/leftTicket/query"
                params = {
                    "leftTicketDTO.train_date": query_date,
                    "leftTicketDTO.from_station": from_station,
                    "leftTicketDTO.to_station": to_station,
                    "purpose_codes": "ADULT"
                }
                
                # 发送请求
                response = client.get(url, params=params, max_retries=3)
                result = response.json()
                
                # 处理查询结果
                if result.get("status"):
                    data = result.get("data", {})
                    result_list = data.get("result", [])
                    
                    # 遍历车次
                    for item in result_list:
                        fields = item.split("|")
                        if len(fields) < 30:
                            continue
                        
                        train_number = fields[3]
                        start_station_code = fields[6]
                        end_station_code = fields[7]
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
                        
                        # 检查车类型
                        train_type = "普通列车"
                        if train_number.startswith("G") or train_number.startswith("C"):
                            train_type = "高铁"
                        elif train_number.startswith("D"):
                            train_type = "动车"
                        
                        # 检查是否符合车类型要求
                        if "全部" not in train_types and train_type not in train_types:
                            continue
                        
                        # 检查是否符合车次要求
                        if selected_trains and train_number not in selected_trains:
                            continue
                        
                        # 检查是否有符合条件的座位
                        available_seats = []
                        for seat_class in seat_classes:
                            if seat_class in remaining_tickets:
                                seat_status = remaining_tickets[seat_class]
                                if seat_status != "无" and seat_status != "":
                                    available_seats.append(f"{seat_class}: {seat_status}")
                        
                        # 如果有符合条件的座位，发送通知
                        if available_seats:
                            message = f"发现符合条件的余票！\n车次: {train_number}\n出发: {start_station_name} {start_time}\n到达: {end_station_name} {end_time}\n历时: {duration}\n余票: {', '.join(available_seats)}"
                            logger.info(message)
                            
                            # 发送邮件通知
                            send_email_notification(message)
                            
                            # 在主线程中显示通知
                            logger.info("准备显示余票通知")
                            # 使用QApplication.postEvent发送事件，在主线程中显示通知
                            class NotificationEvent(QEvent):
                                def __init__(self, message):
                                    super().__init__(QEvent.User)
                                    self.message = message
                            
                            event = NotificationEvent(message)
                            QApplication.postEvent(self, event)
                            
                            # 发现余票后自动停止盯票
                            logger.info("发现余票，自动停止盯票任务")
                            self.auto_track_running = False
                            
                            # 启用所有配置控件
                            def enable_controls():
                                if hasattr(self, 'enable_config_controls'):
                                    self.enable_config_controls()
                            
                            # 在主线程中启用配置控件
                            QTimer.singleShot(0, enable_controls)
                            
                            # 发送事件更新状态
                            class StatusUpdateEvent(QEvent):
                                def __init__(self):
                                    super().__init__(QEvent.User)
                            
                            event = StatusUpdateEvent()
                            QApplication.postEvent(self, event)
                            
                            # 立即跳出所有循环
                            return
                
            except Exception as e:
                logger.error(f"自动盯票任务异常: {e}")
            
            # 随机选择等待时间
            random_interval = random.randint(min_interval, max_interval)
            logger.info(f"本次查询完成，将在 {random_interval} 秒后进行下一次查询")
            
            # 等待下一次查询
            for _ in range(random_interval):
                if not self.auto_track_running:
                    break
                time.sleep(1)
        
        logger.info("自动盯票任务已停止")
        
        # 更新主界面的自动盯票状态标签
        QTimer.singleShot(0, lambda: self.update_auto_track_status())
    
    def show_ticket_notification(self, message):
        """
        显示车票通知
        
        Args:
            message: 通知消息
        """
        logger.info("开始显示余票通知弹窗")
        # 使用critical类型的消息框，确保弹窗醒目且不会被忽略
        QMessageBox.critical(self, "余票通知", message)
        logger.info("余票通知弹窗显示完成")
    
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
        # 禁用自动盯票按钮
        self.auto_track_button.setEnabled(False)
        # 禁用导出Excel按钮
        self.export_excel_button.setEnabled(False)
        # 禁用导出CSV按钮
        self.export_csv_button.setEnabled(False)
        # 禁用清空结果按钮
        self.clear_button.setEnabled(False)
        # 禁用清理日志按钮并设置为灰色
        self.clear_logs_button.setEnabled(False)
        self.clear_logs_button.setStyleSheet("background-color: gray; color: white;")
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
        # 启用自动盯票按钮
        self.auto_track_button.setEnabled(True)
        # 启用导出Excel按钮（需要有查询结果才真正启用）
        self.export_excel_button.setEnabled(False)
        # 启用导出CSV按钮（需要有查询结果才真正启用）
        self.export_csv_button.setEnabled(False)
        # 启用清空结果按钮
        self.clear_button.setEnabled(True)
        # 启用清理日志按钮并设置为紫色
        self.clear_logs_button.setEnabled(True)
        self.clear_logs_button.setStyleSheet("background-color: purple; color: white;")
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
    
    def load_settings(self):
        """
        加载保存的设置
        """
        import json
        import os
        
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 加载出发点、目的地
                if 'start_city' in settings:
                    start_city = settings['start_city']
                    index = self.start_city.findText(start_city)
                    if index >= 0:
                        self.start_city.setCurrentIndex(index)
                
                if 'start_station' in settings:
                    start_station = settings['start_station']
                    index = self.start_station.findText(start_station)
                    if index >= 0:
                        self.start_station.setCurrentIndex(index)
                
                if 'end_city' in settings:
                    end_city = settings['end_city']
                    index = self.end_city.findText(end_city)
                    if index >= 0:
                        self.end_city.setCurrentIndex(index)
                
                if 'end_station' in settings:
                    end_station = settings['end_station']
                    index = self.end_station.findText(end_station)
                    if index >= 0:
                        self.end_station.setCurrentIndex(index)
                
                # 加载出发日期
                if 'query_date' in settings:
                    query_date = settings['query_date']
                    try:
                        date = QDate.fromString(query_date, 'yyyy-MM-dd')
                        if date.isValid():
                            self.query_date.setDate(date)
                    except Exception as e:
                        logger.error(f"解析日期失败: {e}")
                
                # 加载车次类型
                if 'train_type' in settings:
                    train_type = settings['train_type']
                    index = self.train_type.findText(train_type)
                    if index >= 0:
                        self.train_type.setCurrentIndex(index)
                
                # 加载自动盯票配置
                if 'auto_track_config' in settings:
                    self.auto_track_config.update(settings['auto_track_config'])
                
                # 加载夜晚模式设置
                if 'night_mode' in settings:
                    self.is_night_mode = settings['night_mode']
                    if self.is_night_mode:
                        self.night_mode_button.setText("白天模式")
                        self.apply_night_mode()
                    else:
                        self.night_mode_button.setText("夜晚模式")
                        self.apply_day_mode()
                
                logger.info("成功加载保存的设置")
            except Exception as e:
                logger.error(f"加载设置失败: {e}")
        else:
            logger.info("未找到保存的设置文件")
    
    def save_settings(self):
        """
        保存当前设置
        """
        import json
        import os
        
        settings = {
            'start_city': self.start_city.currentText(),
            'start_station': self.start_station.currentText(),
            'end_city': self.end_city.currentText(),
            'end_station': self.end_station.currentText(),
            'query_date': self.query_date.date().toString('yyyy-MM-dd'),
            'train_type': self.train_type.currentText(),
            'auto_track_config': self.auto_track_config,
            'night_mode': self.is_night_mode
        }
        
        settings_file = 'settings.json'
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info("成功保存设置")
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
    
    def toggle_email_fields(self, state):
        """
        根据邮箱提醒复选框的状态，控制邮箱相关控件的启用/禁用状态
        
        Args:
            state: 复选框状态（Qt.Checked 或 Qt.Unchecked）
        """
        enabled = state == Qt.Checked
        self.email_address_edit.setEnabled(enabled)
        self.email_password_edit.setEnabled(enabled)
        self.remember_email_checkbox.setEnabled(enabled)
    
    def disable_config_controls(self):
        """
        禁用所有配置控件
        """
        # 禁用车类型复选框
        for checkbox in self.train_type_checkboxes.values():
            checkbox.setEnabled(False)
        
        # 禁用座位等级复选框
        for checkbox in self.seat_class_checkboxes.values():
            checkbox.setEnabled(False)
        
        # 禁用查询间隔设置
        self.min_interval_spinbox.setEnabled(False)
        self.max_interval_spinbox.setEnabled(False)
        
        # 禁用邮箱相关控件
        self.email_alert_checkbox.setEnabled(False)
        self.email_address_edit.setEnabled(False)
        self.email_password_edit.setEnabled(False)
        self.remember_email_checkbox.setEnabled(False)
        
        # 禁用车次表格
        if hasattr(self, 'train_table'):
            self.train_table.setEnabled(False)
    
    def enable_config_controls(self):
        """
        启用所有配置控件
        """
        # 启用车类型复选框
        for checkbox in self.train_type_checkboxes.values():
            checkbox.setEnabled(True)
        
        # 启用座位等级复选框
        for checkbox in self.seat_class_checkboxes.values():
            checkbox.setEnabled(True)
        
        # 启用查询间隔设置
        self.min_interval_spinbox.setEnabled(True)
        self.max_interval_spinbox.setEnabled(True)
        
        # 启用邮箱相关控件
        self.email_alert_checkbox.setEnabled(True)
        # 根据邮箱提醒是否启用，设置其他邮箱控件的启用状态
        self.toggle_email_fields(self.email_alert_checkbox.checkState())
        
        # 启用车次表格
        if hasattr(self, 'train_table'):
            self.train_table.setEnabled(True)
    
    def update_query_count(self, count):
        """
        更新查询次数显示
        
        Args:
            count: 查询次数
        """
        if hasattr(self, 'query_count_label'):
            self.query_count_label.setText(f"查询次数: {count}")
    
    def show_help(self):
        """
        显示使用说明
        """
        help_message = """
车票自动获取工具 V1.0.1

使用说明：
1. 启动软件后，请先点击"检测网络"按钮，确保网络连接正常
2. 选择出发城市和具体站点
3. 选择目的城市和具体站点
4. 选择出发日期
5. 选择车次类型（可选）
6. 点击"立即查询"按钮，获取直达车次信息
7. 点击"查询中转车次"按钮，获取中转车次信息
8. 点击"自动盯票"按钮，配置并启动自动盯票功能
   - 只能盯直达票，中转票不支持
   - 自动查询间隔不能低于30秒
   - 可配置邮箱提醒功能，当发现余票时发送邮件通知
   - 自动盯票启动后，主界面会实时显示查询次数
   - 配置步骤：
     a. 选择需要监控的车类型（可多选）
     b. 选择需要监控的座位等级（可多选）
     c. 设置查询间隔（不能低于30秒）
     d. 可选择性地选择特定车次进行监控
     e. 配置邮箱提醒功能（可选）：
        - 勾选"启用邮箱提醒"
        - 输入邮箱地址
        - 输入邮箱授权码（不是登录密码）
        - 勾选"记住邮箱配置"以保存邮箱信息
     f. 点击"开始盯票"按钮启动自动盯票
9. 查询结果可以导出为Excel或CSV格式

注意事项：
- 本软件使用12306官方接口获取车票信息
- 为避免被12306反爬机制限制，查询间隔会自动控制
- 自动盯票功能的查询间隔不能低于30秒，以防止对12306服务器造成负担
- 邮箱提醒功能需要使用邮箱授权码，而不是登录密码
- 如遇查询失败，请检查网络连接后重试
- 自动盯票启动后，配置窗口中的设置会变为不可选状态，直到停止盯票或盯票成功
- 当发现余票时，软件会弹出通知，并在开启邮箱提醒的情况下发送邮件通知

版本信息：
- 版本：V1.0.2
- 发布日期：2026-02-16
- 功能：直达车次查询、中转车次查询、自动盯票、邮箱提醒、网络检测、查询次数实时更新
        """
        QMessageBox.information(self, "使用说明", help_message)
    
    def closeEvent(self, event):
        """
        关闭事件
        """
        # 保存当前设置
        self.save_settings()
        
        # 停止定时任务
        if self.scheduled_task_id:
            scheduler.remove_task(self.scheduled_task_id)
        scheduler.stop()
        
        # 关闭网络客户端
        client.close()
        
        event.accept()
    
    def clear_logs(self):
        """
        清理日志文件并释放内存
        """
        import os
        import logging
        from PyQt5.QtWidgets import QMessageBox
        from logger.logger import setup_logger
        
        try:
            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认清理",
                "确定要清理日志文件吗？这将删除所有日志记录。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 关闭当前日志记录器的所有处理器
                global logger
                if logger.handlers:
                    for handler in logger.handlers:
                        handler.close()
                    logger.handlers.clear()
                
                # 删除日志文件
                log_file = "train_get.log"
                if os.path.exists(log_file):
                    try:
                        os.remove(log_file)
                        print("已删除日志文件: train_get.log")
                    except Exception as e:
                        print(f"删除日志文件时出错: {e}")
                
                # 清理debug文件夹中的文件
                debug_dir = "debug"
                if os.path.exists(debug_dir):
                    for file in os.listdir(debug_dir):
                        file_path = os.path.join(debug_dir, file)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print(f"删除debug文件时出错: {e}")
                    print("已清理debug文件夹中的所有文件")
                
                # 重新初始化日志记录器
                logger = setup_logger()
                
                # 显示成功消息
                QMessageBox.information(self, "成功", "日志文件已清理成功！")
                self.status_bar.showMessage("日志文件已清理成功")
                
                # 释放内存
                import gc
                gc.collect()
                
        except Exception as e:
            print(f"清理日志时出错: {e}")
            QMessageBox.critical(self, "错误", f"清理日志时出错: {e}")
    
    def toggle_night_mode(self):
        """
        切换白天/夜晚模式
        """
        # 切换夜晚模式标志
        self.is_night_mode = not self.is_night_mode
        
        # 更新按钮文本
        if self.is_night_mode:
            self.night_mode_button.setText("白天模式")
            # 应用夜晚模式样式
            self.apply_night_mode()
        else:
            self.night_mode_button.setText("夜晚模式")
            # 应用白天模式样式
            self.apply_day_mode()
    
    def apply_night_mode(self):
        """
        应用夜晚模式样式
        """
        # 主窗口背景
        self.setStyleSheet('''.QMainWindow {
            background-color: #2c2c2c;
            color: #e0e0e0;
        }
        
        QGroupBox {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #e0e0e0;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        
        QPushButton {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 5px 10px;
        }
        
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        
        QPushButton:pressed {
            background-color: #6a6a6a;
        }
        
        QPushButton:disabled {
            background-color: #333;
            color: #888;
        }
        
        QLineEdit, QComboBox, QDateEdit, QSpinBox {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 5px;
        }
        
        QTableWidget {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #555;
        }
        
        QTableWidget::item {
            background-color: #3c3c3c;
            color: #e0e0e0;
        }
        
        QTableWidget::item:selected {
            background-color: #5a5a5a;
            color: #e0e0e0;
        }
        
        QHeaderView::section {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #555;
            padding: 5px;
        }
        
        QProgressBar {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 3px;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        
        QStatusBar {
            background-color: #2c2c2c;
            color: #e0e0e0;
            border-top: 1px solid #555;
        }
        
        QCheckBox {
            color: #e0e0e0;
        }
        ''')
        
        # 更新查询次数标签样式
        self.query_count_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        
        # 更新检测网络按钮样式
        if hasattr(self, 'test_network_button'):
            if "background-color: green" in self.test_network_button.styleSheet():
                self.test_network_button.setStyleSheet("background-color: #4CAF50; color: white;")
            elif "background-color: purple" in self.test_network_button.styleSheet():
                self.test_network_button.setStyleSheet("background-color: #9c27b0; color: white;")
    
    def apply_day_mode(self):
        """
        应用白天模式样式
        """
        # 重置为默认样式
        self.setStyleSheet("")
        
        # 更新查询次数标签样式
        self.query_count_label.setStyleSheet("font-weight: bold; color: blue;")
        
        # 更新检测网络按钮样式
        if hasattr(self, 'test_network_button'):
            if "background-color: #4CAF50" in self.test_network_button.styleSheet():
                self.test_network_button.setStyleSheet("background-color: green; color: white;")
            elif "background-color: #9c27b0" in self.test_network_button.styleSheet():
                self.test_network_button.setStyleSheet("background-color: purple; color: white;")
            else:
                self.test_network_button.setStyleSheet("background-color: red; color: white;")
