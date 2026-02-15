import requests
import json
import re
import os
import logging

logger = logging.getLogger('train_get')

class StationParser:
    """
    站点信息解析器，用于从12306官网获取和解析站点信息
    """
    
    def __init__(self):
        self.station_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        self.station_file = os.path.join(os.path.dirname(__file__), "../data/stations.json")
        self.stations = {}
        self.code_to_station = {}
        self.load_stations()
    
    def load_stations(self):
        """
        加载站点信息
        优先从本地文件加载，如果本地文件不存在则从官网获取
        """
        if os.path.exists(self.station_file):
            try:
                with open(self.station_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stations = data.get('stations', {})
                    self.code_to_station = data.get('code_to_station', {})
                logger.info(f"从本地文件加载了 {len(self.stations)} 个站点信息")
            except Exception as e:
                logger.error(f"加载本地站点文件失败: {e}")
                self.fetch_stations()
        else:
            self.fetch_stations()
    
    def fetch_stations(self):
        """
        从12306官网获取站点信息
        """
        logger.info("从12306官网获取站点信息...")
        try:
            response = requests.get(self.station_url, timeout=30)
            response.encoding = 'utf-8'
            content = response.text
            
            # 解析站点信息
            self._parse_station_content(content)
            
            # 保存到本地文件
            self.save_stations()
            
            logger.info(f"成功获取并解析了 {len(self.stations)} 个站点信息")
        except Exception as e:
            logger.error(f"获取站点信息失败: {e}")
    
    def _parse_station_content(self, content):
        """
        解析站点信息内容
        
        Args:
            content: 站点信息内容
        """
        # 提取站点信息部分
        match = re.search(r'var station_names =\'(.*?)\';', content)
        if match:
            station_data = match.group(1)
            station_items = station_data.split('@')
            
            for item in station_items:
                if not item:
                    continue
                
                fields = item.split('|')
                if len(fields) >= 5:
                    station_code = fields[2]  # 站点编码（如VAP）
                    station_name = fields[1]  # 站点名称（如北京北）
                    
                    # 添加到映射中
                    self.stations[station_name] = station_code
                    self.code_to_station[station_code] = station_name
    
    def save_stations(self):
        """
        保存站点信息到本地文件
        """
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(__file__), "../data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 保存站点信息
        data = {
            'stations': self.stations,
            'code_to_station': self.code_to_station
        }
        
        with open(self.station_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"站点信息已保存到 {self.station_file}")
    
    def get_station_code(self, station_name):
        """
        根据站点名称获取站点编码
        
        Args:
            station_name: 站点名称
        
        Returns:
            str: 站点编码，如果不存在则返回站点名称
        """
        return self.stations.get(station_name, station_name)
    
    def get_station_name(self, station_code):
        """
        根据站点编码获取站点名称
        
        Args:
            station_code: 站点编码
        
        Returns:
            str: 站点名称，如果不存在则返回站点编码
        """
        return self.code_to_station.get(station_code, station_code)
    
    def get_all_stations(self):
        """
        获取所有站点名称
        
        Returns:
            list: 站点名称列表
        """
        return list(self.stations.keys())
    
    def get_cities(self):
        """
        获取所有城市名称
        
        Returns:
            list: 城市名称列表
        """
        cities = set()
        for station_name in self.stations.keys():
            # 提取城市名称（取站点名称的前两个字，通常是城市名称）
            city_name = station_name[:2]
            cities.add(city_name)
        return sorted(list(cities))
    
    def get_stations_by_city(self, city_name):
        """
        根据城市名称获取该城市的所有站点
        
        Args:
            city_name: 城市名称
        
        Returns:
            list: 站点名称列表
        """
        stations = []
        for station_name in self.stations.keys():
            if station_name.startswith(city_name):
                stations.append(station_name)
        return sorted(stations)
    
    def update_stations(self):
        """
        更新站点信息
        """
        self.fetch_stations()

# 创建全局实例
station_parser = StationParser()
