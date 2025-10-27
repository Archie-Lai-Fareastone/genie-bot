"""
集中式日誌設定模組

提供統一的日誌設定和 logger 實例建立函式。
確保整個應用程式使用一致的日誌格式和設定。
"""

import logging
import sys
from typing import Optional


# 全域變數，確保 setup_logging 只執行一次
_logging_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    設定全域日誌記錄設定
    
    此函式應該在應用程式啟動時呼叫一次，
    之後所有模組的 logger 都會使用這個設定。
    
    Args:
        level: 日誌記錄層級，預設為 INFO
        
    Examples:
        >>> from src.utils.logger_config import setup_logging
        >>> setup_logging()  # 在應用程式進入點呼叫
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # 設定根 logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # 輸出到控制台
        ],
        force=True  # 強制重新設定，覆蓋任何現有設定
    )
    
    _logging_configured = True
    
    # 記錄日誌系統已初始化
    root_logger = logging.getLogger()
    root_logger.info("日誌系統已初始化")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    取得 logger 實例
    
    Args:
        name: logger 名稱，通常使用模組的 __name__
              如果為 None，則回傳根 logger
        
    Returns:
        logging.Logger: logger 實例
        
    Examples:
        >>> from src.utils.logger_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("這是一條日誌訊息")
    """
    return logging.getLogger(name)


def set_log_level(level: int, logger_name: Optional[str] = None) -> None:
    """
    動態調整日誌層級
    
    Args:
        level: 新的日誌層級 (logging.DEBUG, logging.INFO, 等)
        logger_name: 要調整的 logger 名稱，如果為 None 則調整根 logger
        
    Examples:
        >>> from src.utils.logger_config import set_log_level
        >>> import logging
        >>> set_log_level(logging.DEBUG)  # 設定為 DEBUG 層級
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.info(f"日誌層級已調整為 {logging.getLevelName(level)}")
