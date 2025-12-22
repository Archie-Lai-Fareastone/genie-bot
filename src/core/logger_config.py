"""
集中式日誌設定模組

提供統一的日誌設定和 logger 實例建立函式。
確保整個應用程式使用一致的日誌格式和設定。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


# 全域變數，確保 setup_logging 只執行一次
_logging_configured = False


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    設定全域日誌記錄設定

    此函式應該在應用程式啟動時呼叫一次，
    之後所有模組的 logger 都會使用這個設定。

    Args:
        level: 日誌記錄層級，預設為 INFO
        log_file: 日誌檔案路徑，如果為 None 則使用預設路徑 'logs/app.log'

    Examples:
        >>> from src.core.logger_config import setup_logging
        >>> setup_logging()  # 在應用程式進入點呼叫
        >>> setup_logging(log_file='logs/custom.log')  # 自訂日誌檔案路徑
    """
    global _logging_configured

    if _logging_configured:
        return

    # 設定日誌檔案路徑
    if log_file is None:
        log_file = "logs/app.log"

    # 建立 logs 目錄（如果不存在）
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 建立處理器列表
    handlers = [
        logging.StreamHandler(sys.stdout),  # 輸出到控制台
        RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # 保留 5 個備份檔案
            encoding="utf-8",
        ),
    ]

    # 設定根 logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # 強制重新設定，覆蓋任何現有設定
    )

    _logging_configured = True

    # 抑制 Azure HTTP 請求/回應的詳細日誌
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )
    logging.getLogger("azure.identity").setLevel(logging.DEBUG)

    # 記錄日誌系統已初始化
    root_logger = logging.getLogger()
    root_logger.info(f"日誌系統已初始化，日誌檔案: {log_file}")


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
