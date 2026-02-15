# 车票信息自动获取应用

## 项目简介

这是一款使用Python开发的桌面端车票信息自动获取应用，支持从12306网站抓取车票信息，提供定时查询、结果导出等功能。

## 功能特点

- **多种车次类型支持**：支持高铁、动车、普通列车等多种车次类型的信息获取
- **自定义查询参数**：可设置出发地、目的地、日期等关键参数
- **定时自动查询**：支持设置查询频率和时间范围
- **健壮的反爬机制**：包括合理的请求间隔设置、User-Agent随机切换等
- **直观的用户界面**：使用PyQt开发，布局清晰，操作简单
- **查询结果导出**：支持导出为Excel和CSV格式
- **完善的日志记录**：便于问题排查和维护

## 技术架构

- **开发语言**：Python 3.7+
- **GUI框架**：PyQt5
- **网络请求**：requests
- **网页解析**：BeautifulSoup4 + lxml
- **定时任务**：schedule
- **数据处理**：pandas
- **日志记录**：logging

## 项目结构

```
TrainGet/
├── network/          # 网络请求模块
│   ├── __init__.py
│   └── client.py      # 网络请求客户端
├── parser/           # 网页解析模块
│   ├── __init__.py
│   └── ticket_parser.py  # 车票信息解析器
├── scheduler/        # 定时任务模块
│   ├── __init__.py
│   └── task_scheduler.py  # 任务调度器
├── gui/              # 桌面界面模块
│   ├── __init__.py
│   └── main_window.py  # 主窗口
├── exporter/         # 数据导出模块
│   ├── __init__.py
│   └── exporter.py    # 数据导出器
├── logger/           # 日志记录模块
│   ├── __init__.py
│   └── logger.py      # 日志设置
├── utils/            # 工具模块
│   ├── __init__.py
│   └── test_parser.py  # 解析测试
├── main.py           # 应用入口
├── test.py           # 测试脚本
├── requirements.txt  # 依赖管理
└── README.md         # 项目说明
```

## 安装说明

### 1. 克隆项目

```bash
git clone <repository-url>
cd TrainGet
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 运行应用

```bash
python main.py
```

### 2. 设置查询条件

- **出发地**：输入出发城市名称（如：北京）
- **目的地**：输入到达城市名称（如：上海）
- **出发日期**：选择出发日期
- **车次类型**：选择车次类型（全部、高铁、动车、普通列车）

### 3. 执行查询

- **立即查询**：点击按钮执行单次查询
- **定时查询**：点击按钮启动定时查询（每5分钟执行一次）

### 4. 导出结果

- **导出Excel**：将查询结果导出为Excel文件
- **导出CSV**：将查询结果导出为CSV文件

### 5. 清空结果

- **清空结果**：点击按钮清空当前查询结果

## 注意事项

1. 本应用仅用于学习和研究目的，请勿用于商业用途
2. 使用时请遵守12306网站的使用条款和相关法律法规
3. 频繁查询可能会被网站限制，建议合理设置查询间隔
4. 如遇网页结构变化，可能需要更新解析规则

## 故障排查

1. **网络连接失败**：检查网络连接是否正常，防火墙是否阻止了请求
2. **解析失败**：可能是12306网站结构发生了变化，需要更新解析规则
3. **导出失败**：检查目标文件夹是否有写入权限
4. **定时任务不执行**：检查是否有其他程序占用了系统资源

## 日志文件

应用运行过程中的日志会记录在`train_get.log`文件中，可用于排查问题。

## 开发与测试

### 运行测试

```bash
python test.py
```

### 代码结构说明

- **network/client.py**：实现网络请求和反爬机制
- **parser/ticket_parser.py**：实现网页解析和信息提取
- **scheduler/task_scheduler.py**：实现定时任务管理
- **gui/main_window.py**：实现桌面端用户界面
- **exporter/exporter.py**：实现数据导出功能
- **logger/logger.py**：实现日志记录功能

## 版本历史

- **v1.0.0**：初始版本，实现基本功能

## 许可证

本项目采用MIT许可证，详见LICENSE文件。
