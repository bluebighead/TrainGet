#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络请求模块，包含反爬机制
"""

import time
import random
import requests
from logger.logger import setup_logger
from utils.station_parser import station_parser

# 设置日志
logger = setup_logger()


class NetworkClient:
    """网络请求客户端，包含反爬机制"""
    
    # 常见的User-Agent列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70"
    ]
    
    def __init__(self, base_url="https://kyfw.12306.cn", timeout=30):
        """
        初始化网络客户端
        
        Args:
            base_url: 基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_interval = 2  # 最小请求间隔（秒）
        # 使用station_parser获取站点信息
        logger.info(f"已加载 {len(station_parser.get_all_stations())} 个站点信息")
        # 初始化会话，访问首页获取Cookie
        self._init_session()
    
    def _get_random_user_agent(self):
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    def _init_session(self):
        """
        初始化会话，访问首页获取Cookie和会话信息
        """
        try:
            logger.info("1. 访问12306首页获取会话信息...")
            index_url = "https://kyfw.12306.cn/otn/"
            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            response = self.session.get(index_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"首页访问成功，状态码: {response.status_code}")
            
            # 访问余票查询页面
            logger.info("2. 访问余票查询页面获取Cookie...")
            left_ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
            response = self.session.get(left_ticket_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"余票查询页面访问成功，状态码: {response.status_code}")
            
            # 随机等待一段时间
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"初始化会话失败: {e}")
            # 即使失败也继续执行，后续请求会重新创建会话
    
    def _wait_for_interval(self):
        """等待请求间隔"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def get(self, url, params=None, headers=None, max_retries=3):
        """
        发送GET请求，支持重试
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 请求头
            max_retries: 最大重试次数
        
        Returns:
            response: 响应对象
        """
        for retry in range(max_retries):
            try:
                # 等待请求间隔
                self._wait_for_interval()
                
                # 构建请求头
                default_headers = {
                    "User-Agent": self._get_random_user_agent(),
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
                    "Sec-Ch-Ua-Platform": "\"Windows\"",
                    "DNT": "1",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://kyfw.12306.cn/",
                    "Origin": "https://kyfw.12306.cn"
                }
                
                if headers:
                    default_headers.update(headers)
                
                # 发送请求
                logger.info(f"发送GET请求: {url}, 参数: {params}, 重试次数: {retry+1}/{max_retries}")
                response = self.session.get(
                    url,
                    params=params,
                    headers=default_headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=True
                )
                
                # 检查响应状态
                response.raise_for_status()
                
                logger.info(f"请求成功: {url}, 状态码: {response.status_code}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败: {url}, 错误: {e}")
                if retry < max_retries - 1:
                    logger.info(f"正在重试... ({retry+2}/{max_retries})")
                    # 增加等待时间，随着重试次数增加而增加
                    wait_time = random.uniform(2 + retry, 4 + retry)
                    time.sleep(wait_time)
                    # 重新创建会话，避免使用被封禁的会话
                    self.session = requests.Session()
                else:
                    raise
    
    def post(self, url, data=None, json=None, headers=None):
        """
        发送POST请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
        
        Returns:
            response: 响应对象
        """
        try:
            # 等待请求间隔
            self._wait_for_interval()
            
            # 构建请求头
            default_headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Connection": "keep-alive"
            }
            
            if headers:
                default_headers.update(headers)
            
            # 发送请求
            logger.info(f"发送POST请求: {url}")
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=default_headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            logger.info(f"请求成功: {url}, 状态码: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            raise
    
    def get_station_code(self, station_name):
        """
        获取站点编码
        
        Args:
            station_name: 站点名称
        
        Returns:
            str: 站点编码，如果不存在则返回站点名称
        """
        return station_parser.get_station_code(station_name)
    
    def get_station_name(self, station_code):
        """
        获取站点名称
        
        Args:
            station_code: 站点编码
        
        Returns:
            str: 站点名称，如果不存在则返回站点编码
        """
        return station_parser.get_station_name(station_code)
    
    def query_transfer_tickets(self, start_station, end_station, query_date, max_transfers=1):
        """
        查询中转车次
        
        Args:
            start_station: 出发地
            end_station: 目的地
            query_date: 查询日期
            max_transfers: 最大中转次数
        
        Returns:
            list: 中转车次列表
        """
        import json
        
        # 获取站点编码
        from_station = self.get_station_code(start_station)
        to_station = self.get_station_code(end_station)
        
        # 构建查询URL
        url = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": query_date,
            "leftTicketDTO.from_station": from_station,
            "leftTicketDTO.to_station": to_station,
            "purpose_codes": "ADULT"
        }
        
        # 添加额外的请求头
        extra_headers = {
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        # 生成中转方案
        transfer_plans = []
        
        # 手动添加常用中转站
        common_transfer_stations = [
            "NNZ",  # 南宁
            "GLZ",  # 桂林
            "GBZ",  # 桂林北
            "LZQ",  # 柳州
            "HZH",  # 杭州
            "SHH",  # 上海
            "BJP"   # 北京
        ]
        
        # 过滤掉起点和终点
        transfer_stations = [station for station in common_transfer_stations if station not in [from_station, to_station]]
        logger.info(f"使用 {len(transfer_stations)} 个常用中转站")
        
        # 查询出发地到中转站的车次
        for transfer_station in transfer_stations:
            # 查询出发地到中转站
            transfer_params = {
                "leftTicketDTO.train_date": query_date,
                "leftTicketDTO.from_station": from_station,
                "leftTicketDTO.to_station": transfer_station,
                "purpose_codes": "ADULT"
            }
            
            try:
                transfer_response = self.get(url, params=transfer_params, headers=extra_headers, max_retries=3)
                transfer_result = transfer_response.json()
                
                if transfer_result.get("status"):
                    transfer_data = transfer_result.get("data", {})
                    transfer_result_list = transfer_data.get("result", [])
                    
                    if not transfer_result_list:
                        logger.info(f"从 {start_station} 到中转站 {self.get_station_name(transfer_station)} 没有直达车次")
                        continue
                    
                    # 查询中转站到目的地
                    dest_params = {
                        "leftTicketDTO.train_date": query_date,
                        "leftTicketDTO.from_station": transfer_station,
                        "leftTicketDTO.to_station": to_station,
                        "purpose_codes": "ADULT"
                    }
                    
                    dest_response = self.get(url, params=dest_params, headers=extra_headers, max_retries=3)
                    dest_result = dest_response.json()
                    
                    if dest_result.get("status"):
                        dest_data = dest_result.get("data", {})
                        dest_result_list = dest_data.get("result", [])
                        
                        if not dest_result_list:
                            logger.info(f"从中转站 {self.get_station_name(transfer_station)} 到 {end_station} 没有直达车次")
                            continue
                        
                        logger.info(f"从 {start_station} 到 {self.get_station_name(transfer_station)} 有 {len(transfer_result_list)} 个车次")
                        logger.info(f"从 {self.get_station_name(transfer_station)} 到 {end_station} 有 {len(dest_result_list)} 个车次")
                        
                        # 匹配中转方案
                        for first_train in transfer_result_list:
                            first_fields = first_train.split("|")
                            if len(first_fields) < 30:
                                continue
                            
                            first_train_number = first_fields[3]
                            first_start_time = first_fields[8]
                            first_end_time = first_fields[9]
                            first_start_station_name = self.get_station_name(first_fields[6])
                            first_end_station_name = self.get_station_name(first_fields[7])
                            
                            # 解析余票信息
                            first_remaining_tickets = {
                                "商务座": first_fields[32] if first_fields[32] != "" else "无",
                                "一等座": first_fields[31] if first_fields[31] != "" else "无",
                                "二等座": first_fields[30] if first_fields[30] != "" else "无",
                                "硬卧": first_fields[28] if first_fields[28] != "" else "无",
                                "硬座": first_fields[29] if first_fields[29] != "" else "无",
                                "软卧": first_fields[23] if first_fields[23] != "" else "无",
                                "站票": first_fields[26] if len(first_fields) > 26 and first_fields[26] != "" else "无"
                            }
                            
                            for second_train in dest_result_list:
                                second_fields = second_train.split("|")
                                if len(second_fields) < 30:
                                    continue
                                
                                second_train_number = second_fields[3]
                                second_start_time = second_fields[8]
                                second_end_time = second_fields[9]
                                second_start_station_name = self.get_station_name(second_fields[6])
                                second_end_station_name = self.get_station_name(second_fields[7])
                                
                                # 检查中转时间是否合理（至少20分钟）
                                import datetime
                                first_end_dt = datetime.datetime.strptime(first_end_time, "%H:%M")
                                second_start_dt = datetime.datetime.strptime(second_start_time, "%H:%M")
                                
                                # 计算时间差
                                time_diff = (second_start_dt - first_end_dt).total_seconds() / 60
                                
                                # 处理跨天的情况
                                if time_diff < 0:
                                    # 假设是跨天，加上24小时
                                    time_diff += 24 * 60
                                
                                if time_diff >= 20 and time_diff <= 720:  # 20分钟到12小时
                                    # 解析余票信息
                                    second_remaining_tickets = {
                                        "商务座": second_fields[32] if second_fields[32] != "" else "无",
                                        "一等座": second_fields[31] if second_fields[31] != "" else "无",
                                        "二等座": second_fields[30] if second_fields[30] != "" else "无",
                                        "硬卧": second_fields[28] if second_fields[28] != "" else "无",
                                        "硬座": second_fields[29] if second_fields[29] != "" else "无",
                                        "软卧": second_fields[23] if second_fields[23] != "" else "无",
                                        "站票": second_fields[26] if len(second_fields) > 26 and second_fields[26] != "" else "无"
                                    }
                                    
                                    # 计算总历时
                                    first_duration = first_fields[10]
                                    second_duration = second_fields[10]
                                    
                                    # 解析历时
                                    def parse_duration(duration_str):
                                        if '天' in duration_str:
                                            days, rest = duration_str.split('天')
                                            hours, minutes = rest.split(':')
                                            return int(days)*24*60 + int(hours)*60 + int(minutes)
                                        else:
                                            hours, minutes = duration_str.split(':')
                                            return int(hours)*60 + int(minutes)
                                    
                                    total_duration_minutes = parse_duration(first_duration) + parse_duration(second_duration) + int(time_diff)
                                    
                                    # 格式化为时分
                                    total_hours = total_duration_minutes // 60
                                    total_minutes = total_duration_minutes % 60
                                    total_duration = f"{total_hours}:{total_minutes:02d}"
                                    
                                    # 创建中转方案
                                    transfer_plan = {
                                        "transfers": [
                                            {
                                                "train_number": first_train_number,
                                                "start_station": first_start_station_name,
                                                "end_station": first_end_station_name,
                                                "start_time": first_start_time,
                                                "end_time": first_end_time,
                                                "duration": first_duration,
                                                "remaining_tickets": first_remaining_tickets
                                            },
                                            {
                                                "train_number": second_train_number,
                                                "start_station": second_start_station_name,
                                                "end_station": second_end_station_name,
                                                "start_time": second_start_time,
                                                "end_time": second_end_time,
                                                "duration": second_duration,
                                                "remaining_tickets": second_remaining_tickets
                                            }
                                        ],
                                        "total_duration": total_duration,
                                        "transfer_station": second_start_station_name,
                                        "transfer_time": f"{time_diff:.0f}分钟",
                                        "date": query_date
                                    }
                                    
                                    transfer_plans.append(transfer_plan)
                                    logger.info(f"找到中转方案: {first_train_number} -> {second_train_number}")
            except Exception as e:
                logger.error(f"查询中转车次失败: {e}")
                continue
        
        logger.info(f"找到 {len(transfer_plans)} 个中转方案")
        return transfer_plans
    
    def close(self):
        """关闭会话"""
        self.session.close()


# 创建全局网络客户端实例
client = NetworkClient()
