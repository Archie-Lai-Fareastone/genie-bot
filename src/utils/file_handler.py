"""
檔案附件處理模組

提供檔案附件的提取、驗證和記錄函式。
支援 Microsoft Teams 訊息中的檔案附件處理。
"""

from dataclasses import dataclass
from typing import List, Optional
from botbuilder.schema import Activity
from src.core.logger_config import get_logger

# 取得 logger 實例
logger = get_logger(__name__)

# 支援的檔案類型
SUPPORTED_EXTENSIONS = [".pdf", ".doc", ".docx"]
SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


@dataclass
class FileAttachmentInfo:
    """檔案附件資訊

    Attributes:
        name: 檔案名稱 (例如 "report.pdf")
        download_url: Teams 提供的暫存下載 URL
        file_type: 檔案類型或副檔名 (例如 "pdf")
        is_supported: 是否為支援的檔案類型
    """

    name: str
    download_url: str
    file_type: str
    is_supported: bool


def extract_attachments(activity: Activity) -> List[FileAttachmentInfo]:
    """從 Teams 訊息活動中提取檔案附件

    Args:
        activity: Teams 訊息活動物件

    Returns:
        檔案附件資訊列表
    """
    attachments = []

    if not activity.attachments:
        return attachments

    for attachment in activity.attachments:
        # 檢查是否為 Teams 檔案下載類型
        if (
            attachment.content_type
            == "application/vnd.microsoft.teams.file.download.info"
        ):
            try:
                name = attachment.name or "unknown"
                content = attachment.content or {}
                download_url = content.get("downloadUrl", "")
                file_type = content.get("fileType", "")

                # 驗證檔案類型
                is_supported = _is_file_supported(name, file_type)

                file_info = FileAttachmentInfo(
                    name=name,
                    download_url=download_url,
                    file_type=file_type,
                    is_supported=is_supported,
                )
                attachments.append(file_info)
                logger.debug(
                    f"提取附件: {name}, 類型: {file_type}, 支援: {is_supported}"
                )

            except Exception as e:
                logger.error(f"提取附件時發生錯誤: {e}", exc_info=True)

    return attachments


def _is_file_supported(filename: str, file_type: str) -> bool:
    """檢查檔案是否為支援的類型

    Args:
        filename: 檔案名稱
        file_type: 檔案類型或副檔名

    Returns:
        是否為支援的檔案類型
    """
    # 檢查副檔名
    filename_lower = filename.lower()
    for ext in SUPPORTED_EXTENSIONS:
        if filename_lower.endswith(ext):
            return True

    # 檢查 MIME 類型
    if file_type.lower() in [mime.lower() for mime in SUPPORTED_MIME_TYPES]:
        return True

    return False


def validate_attachments(
    files: List[FileAttachmentInfo],
) -> tuple[List[FileAttachmentInfo], List[FileAttachmentInfo]]:
    """驗證檔案附件類型

    Args:
        files: 檔案附件資訊列表

    Returns:
        (支援的檔案列表, 不支援的檔案列表)
    """
    supported = []
    unsupported = []

    for file_info in files:
        if file_info.is_supported:
            supported.append(file_info)
        else:
            unsupported.append(file_info)

    return supported, unsupported


def log_attachment(
    file_info: FileAttachmentInfo, user_info: Optional[str] = None
) -> None:
    """記錄成功處理的附件

    Args:
        file_info: 檔案附件資訊
        user_info: 使用者資訊 (例如使用者 ID 或電子郵件)
    """
    user_msg = f"from user: {user_info}" if user_info else ""
    logger.info(f"Received file: {file_info.name} {user_msg}".strip())
