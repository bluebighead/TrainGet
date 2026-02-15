#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium调试查询问题
"""

import sys
import os
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger.logger import setup_logger

# 设置日志
logger = setup_logger()

def debug_query():
    """
    使用Selenium调试查询
    """
    logger.info("开始使用Selenium调试查询")
    
    try:
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
        
        # 创建WebDriver实例
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome浏览器启动成功")
        
        # 1. 访问首页
        logger.info("1. 访问12306首页...")
        driver.get("https://kyfw.12306.cn/")
        time.sleep(random.uniform(2, 4))
        logger.info("首页访问成功")
        
        # 2. 访问余票查询页面
        logger.info("2. 访问余票查询页面...")
        driver.get("https://kyfw.12306.cn/otn/leftTicket/init")
        time.sleep(random.uniform(2, 4))
        logger.info("余票查询页面访问成功")
        
        # 3. 直接访问查询接口
        logger.info("3. 访问查询接口...")
        query_url = "https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=2026-02-20&leftTicketDTO.from_station=BHZ&leftTicketDTO.to_station=GLZ&purpose_codes=ADULT"
        driver.get(query_url)
        time.sleep(random.uniform(2, 4))
        logger.info("查询接口访问成功")
        
        # 获取响应内容
        response_text = driver.page_source
        logger.info(f"响应内容长度: {len(response_text)}")
        
        # 保存响应内容到文件
        debug_file = "debug_selenium.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        logger.info(f"响应内容已保存到 {debug_file}")
        
        # 尝试解析JSON
        logger.info("4. 解析响应内容...")
        try:
            # 从响应中提取JSON
            import re
            json_match = re.search(r'\{"status":.*?\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                result = json.loads(json_text)
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
                else:
                    logger.error(f"查询失败，响应状态为False")
                    logger.error(f"响应消息: {result.get('messages')}")
            else:
                logger.error("无法从响应中提取JSON")
                
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            
        finally:
            # 关闭浏览器
            driver.quit()
            logger.info("浏览器已关闭")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_query()
