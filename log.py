# log.py
import logging
import os

# 创建日志文件夹
LOG_DIR = "log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# 配置日志
def get_logger(name: str,is_to_console):
    """
    获取带有指定名称的日志记录器。
    :param name: 日志记录器的名称（通常为模块名）
    :return: 日志记录器
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # 防止重复添加处理器
        logger.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"{name}.log"))
        file_handler.setLevel(logging.INFO)

        # 设置日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        if is_to_console:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 添加处理器到日志记录器
        logger.addHandler(file_handler)


    return logger
