import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name="avatar-player", log_dir="logs", level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name: 日志名称
        log_dir: 日志文件目录
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成带时间戳的日志文件名
    # timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"device_{name}_{timestamp}.log")
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建文件处理器，支持日志轮转（每个文件最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"日志系统已初始化，日志文件: {log_file}")
    
    return logger
