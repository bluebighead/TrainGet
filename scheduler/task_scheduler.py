#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度模块
"""

import threading
import time
import schedule
from logger.logger import setup_logger

# 设置日志
logger = setup_logger()


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        """初始化任务调度器"""
        self.schedule_thread = None
        self.is_running = False
        self.tasks = []
    
    def add_task(self, interval, task_func, *args, **kwargs):
        """
        添加定时任务
        
        Args:
            interval: 执行间隔（秒）
            task_func: 任务函数
            *args: 任务函数参数
            **kwargs: 任务函数关键字参数
        
        Returns:
            str: 任务ID
        """
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        
        # 添加任务到schedule
        def job():
            try:
                logger.info(f"执行定时任务: {task_id}")
                task_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"执行定时任务失败: {e}")
        
        # 根据间隔设置任务
        if interval < 60:
            schedule.every(interval).seconds.do(job)
        elif interval < 3600:
            minutes = interval // 60
            schedule.every(minutes).minutes.do(job)
        else:
            hours = interval // 3600
            schedule.every(hours).hours.do(job)
        
        # 保存任务信息
        self.tasks.append({
            "id": task_id,
            "interval": interval,
            "func": task_func,
            "args": args,
            "kwargs": kwargs
        })
        
        logger.info(f"添加定时任务成功: {task_id}, 间隔: {interval}秒")
        return task_id
    
    def remove_task(self, task_id):
        """
        移除定时任务
        
        Args:
            task_id: 任务ID
        """
        # 移除任务
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        
        # 重新设置所有任务
        schedule.clear()
        for task in self.tasks:
            self.add_task(
                task["interval"],
                task["func"],
                *task["args"],
                **task["kwargs"]
            )
        
        logger.info(f"移除定时任务成功: {task_id}")
    
    def start(self):
        """
        启动任务调度器
        """
        if not self.is_running:
            self.is_running = True
            self.schedule_thread = threading.Thread(target=self._run_schedule, daemon=True)
            self.schedule_thread.start()
            logger.info("任务调度器启动成功")
    
    def stop(self):
        """
        停止任务调度器
        """
        if self.is_running:
            self.is_running = False
            if self.schedule_thread:
                self.schedule_thread.join(timeout=5)
            schedule.clear()
            self.tasks = []
            logger.info("任务调度器停止成功")
    
    def _run_schedule(self):
        """
        运行调度循环
        """
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
                time.sleep(1)
    
    def get_tasks(self):
        """
        获取所有任务
        
        Returns:
            list: 任务列表
        """
        return self.tasks
    
    def clear_all_tasks(self):
        """
        清除所有任务
        """
        schedule.clear()
        self.tasks = []
        logger.info("清除所有定时任务成功")


# 创建全局调度器实例
scheduler = TaskScheduler()
