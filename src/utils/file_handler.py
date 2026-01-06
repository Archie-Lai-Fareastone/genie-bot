"""
檔案處理模組

提供 Microsoft Teams 檔案上傳和 Microsoft Graph API 存取功能
"""

from typing import Optional, List, Dict, Any
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, Attachment, ActivityTypes
from botbuilder.schema.teams import FileConsentCard, FileConsentCardResponse
from urllib.parse import unquote

from src.core.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class UploadedFile:
    """
    代表透過 Teams 上傳的檔案

    Attributes:
        file_id: Teams/OneDrive 的唯一識別碼
        name: 原始檔案名稱
        download_url: 直接下載 URL
        content_type: MIME 類型 (例如: application/pdf)
        size: 檔案大小（位元組）
        local_path: 暫存本地路徑（選填）
        owner_id: 上傳檔案的 Teams 使用者 ID
    """

    file_id: str
    name: str
    download_url: str
    content_type: str
    size: int
    owner_id: str
    local_path: Optional[str] = None


@dataclass
class FileUploadState:
    """
    追蹤對話中多檔案上傳批次的狀態

    Attributes:
        conversation_id: Teams 對話 ID
        expected_files: 預期的檔案數量
        received_files: 已成功同意的檔案清單
        declined_requests: 使用者拒絕的檔案請求數
        status: pending, completed, failed
    """

    conversation_id: str
    expected_files: int = 1
    received_files: List[UploadedFile] = field(default_factory=list)
    declined_requests: int = 0
    status: str = "pending"  # pending, completed, failed


class GraphService:
    """
    Microsoft Graph API 服務類別

    處理身份驗證和令牌快取
    """

    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        """
        初始化 Graph Service

        Args:
            client_id: Azure AD 應用程式 (Service Principal) ID
            client_secret: Azure AD 應用程式密鑰
            tenant_id: Azure AD 租戶 ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = "https://graph.microsoft.com/.default"

        # 令牌快取
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        logger.info("GraphService 已初始化")

    def get_access_token(self) -> str:
        """
        取得 Microsoft Graph API 存取令牌

        使用快取機制避免重複請求

        Returns:
            str: 有效的存取令牌

        Raises:
            Exception: 當無法取得令牌時
        """
        # 檢查快取的令牌是否仍然有效
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                logger.debug("使用快取的存取令牌")
                return self._access_token

        # 請求新的存取令牌
        token_url = f"{self.authority}/oauth2/v2.0/token"
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials",
        }

        try:
            response = requests.post(token_url, data=token_data, timeout=10)
            response.raise_for_status()
            token_response = response.json()

            self._access_token = token_response["access_token"]
            expires_in = token_response.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(
                seconds=expires_in - 300
            )

            logger.info("成功取得新的 Graph API 存取令牌")
            return self._access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"取得 Graph API 存取令牌失敗: {e}", exc_info=True)
            raise Exception(f"無法取得 Graph API 存取令牌: {e}")


class FileHandler:
    """
    檔案處理類別

    封裝 Teams 檔案上傳同意流程和 Graph API 檔案下載
    """

    def __init__(self, graph_service: GraphService):
        """
        初始化 FileHandler

        Args:
            graph_service: GraphService 實例，用於 Graph API 認證
        """
        self.graph_service = graph_service

        # 追蹤對話的上傳狀態
        self._upload_states: Dict[str, FileUploadState] = {}
        self.max_files_per_batch = 5

        logger.info("FileHandler 已初始化")

    async def send_file_consent_card(
        self,
        turn_context: TurnContext,
        filename: str,
        description: Optional[str] = None,
    ) -> None:
        """
        發送檔案同意卡片給使用者

        Args:
            turn_context: Bot 對話上下文
            filename: 建議的檔案名稱
            description: 檔案描述（選填）
        """
        if description is None:
            description = f"請上傳 {filename}"

        file_consent_card = FileConsentCard(
            description=description,
            size_in_bytes=0,  # 未知大小
            accept_context={"filename": filename},
            decline_context={"filename": filename},
        )

        attachment = Attachment(
            content_type="application/vnd.microsoft.teams.card.file.consent",
            name=filename,
            content=file_consent_card,
        )

        reply = Activity(type=ActivityTypes.message, attachments=[attachment])

        await turn_context.send_activity(reply)
        logger.info(f"已發送檔案同意卡片: {filename}")

    async def handle_file_consent_accept(
        self, turn_context: TurnContext, file_consent_response: FileConsentCardResponse
    ) -> UploadedFile:
        """
        處理使用者接受檔案上傳

        Args:
            turn_context: Bot 對話上下文
            file_consent_response: 檔案同意回應

        Returns:
            UploadedFile: 上傳的檔案資訊
        """
        upload_info = file_consent_response.upload_info

        download_url = getattr(upload_info, "content_url", None)
        if not download_url:
            raise ValueError("Teams 未提供 content_url，無法下載檔案")

        file_size = 0
        content_type = "application/octet-stream"
        resolved_name = upload_info.name

        try:
            file_metadata = await self._get_file_metadata_from_url(download_url)
            if file_metadata:
                file_size = file_metadata.get("size", 0)
                content_type = file_metadata.get("content_type", content_type)
                resolved_name = file_metadata.get("file_name", resolved_name)
        except Exception as metadata_error:
            logger.warning(f"無法取得檔案 Metadata: {metadata_error}")

        if (
            content_type == "application/octet-stream"
            and hasattr(upload_info, "file_type")
            and upload_info.file_type
        ):
            content_type = self._get_mime_type(upload_info.file_type)

        uploaded_file = UploadedFile(
            file_id=upload_info.unique_id,
            name=resolved_name,
            download_url=download_url,
            content_type=content_type,
            size=file_size,
            owner_id=turn_context.activity.from_property.id,
        )

        logger.info(
            f"使用者接受檔案上傳: {uploaded_file.name} "
            f"(ID: {uploaded_file.file_id}, Size: {file_size} bytes)"
        )

        return uploaded_file

    async def handle_file_consent_decline(
        self, turn_context: TurnContext, file_consent_response: FileConsentCardResponse
    ) -> Optional[FileUploadState]:
        """
        處理使用者拒絕檔案上傳

        Args:
            turn_context: Bot 對話上下文
            file_consent_response: 檔案同意回應
        """
        logger.info(
            f"使用者拒絕檔案上傳: "
            f"{file_consent_response.context.get('filename', 'unknown')}"
        )

        await turn_context.send_activity("已取消檔案上傳。")

        conversation_id = turn_context.activity.conversation.id
        return self.mark_declined_file(conversation_id)

    async def download_file(self, download_url: str) -> bytes:
        """
        從指定 URL 下載檔案內容

        Args:
            download_url: 檔案下載 URL

        Returns:
            bytes: 檔案內容

        Raises:
            Exception: 當下載失敗時
        """
        try:
            # 取得 Graph API 存取令牌
            access_token = self.graph_service.get_access_token()

            headers = {"Authorization": f"Bearer {access_token}"}

            logger.info(f"開始下載檔案: {download_url[:50]}...")
            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()

            content_length = len(response.content)
            logger.info(f"成功下載檔案，大小: {content_length} bytes")

            # 檢查檔案大小限制（例如：100MB）
            max_file_size = 100 * 1024 * 1024  # 100MB
            if content_length > max_file_size:
                logger.warning(
                    f"檔案大小 ({content_length} bytes) 超過限制 "
                    f"({max_file_size} bytes)"
                )
                raise Exception(
                    f"檔案大小超過限制 ({max_file_size / (1024*1024):.0f}MB)"
                )

            return response.content

        except requests.exceptions.Timeout:
            logger.error("下載檔案超時", exc_info=True)
            raise Exception("下載檔案超時，請稍後再試")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            logger.error(f"HTTP 錯誤 {status_code}: {e}", exc_info=True)
            if status_code == 403:
                raise Exception(
                    "存取被拒絕。請確認 Service Principal 具有 "
                    "Files.Read.All 應用程式權限"
                )
            elif status_code == 404:
                raise Exception("找不到檔案")
            else:
                raise Exception(f"下載檔案時發生 HTTP 錯誤: {status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"下載檔案失敗: {e}", exc_info=True)
            raise Exception(f"無法下載檔案: {e}")

    def get_upload_state(self, conversation_id: str) -> Optional[FileUploadState]:
        """
        取得對話的上傳狀態

        Args:
            conversation_id: Teams 對話 ID

        Returns:
            FileUploadState 或 None
        """
        return self._upload_states.get(conversation_id)

    def create_upload_state(
        self, conversation_id: str, expected_files: int = 1
    ) -> FileUploadState:
        """
        建立新的上傳狀態追蹤

        Args:
            conversation_id: Teams 對話 ID
            expected_files: 預期的檔案數量

        Returns:
            FileUploadState: 新建立的上傳狀態
        """
        state = FileUploadState(
            conversation_id=conversation_id, expected_files=expected_files
        )
        self._upload_states[conversation_id] = state
        logger.info(
            f"建立上傳狀態追蹤: {conversation_id}, 預期檔案數: {expected_files}"
        )
        return state

    def update_upload_state(
        self, conversation_id: str, uploaded_file: UploadedFile
    ) -> FileUploadState:
        """
        更新上傳狀態，加入新的已上傳檔案

        Args:
            conversation_id: Teams 對話 ID
            uploaded_file: 新上傳的檔案

        Returns:
            FileUploadState: 更新後的上傳狀態
        """
        state = self._upload_states.get(conversation_id)
        if not state:
            state = self.create_upload_state(conversation_id)

        state.received_files.append(uploaded_file)

        # 檢查是否所有檔案都已收到
        if len(state.received_files) >= state.expected_files:
            state.status = "completed"
            logger.info(f"上傳批次完成: {conversation_id}")

        return state

    def mark_declined_file(self, conversation_id: str) -> Optional[FileUploadState]:
        """在使用者拒絕時更新批次狀態"""

        state = self._upload_states.get(conversation_id)
        if not state:
            return None

        state.declined_requests += 1

        if state.expected_files > len(state.received_files):
            state.expected_files = max(
                state.expected_files - 1, len(state.received_files)
            )

        if len(state.received_files) >= state.expected_files:
            state.status = "completed"
            logger.info(f"所有檔案請求已完成或取消: {conversation_id}")

        return state

    def clear_upload_state(self, conversation_id: str) -> None:
        """
        清除對話的上傳狀態

        Args:
            conversation_id: Teams 對話 ID
        """
        if conversation_id in self._upload_states:
            del self._upload_states[conversation_id]
            logger.info(f"已清除上傳狀態: {conversation_id}")

    async def _get_file_metadata_from_url(
        self, content_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        從 content_url 取得檔案 Metadata（使用 Graph API）

        Args:
            content_url: Teams 檔案的 content_url

        Returns:
            檔案 Metadata 字典，包含 size、content_type、file_name
        """

        if not content_url:
            return None

        access_token = self.graph_service.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        def _extract_headers(resp_headers: Dict[str, str]) -> Dict[str, Any]:
            metadata: Dict[str, Any] = {}
            size_header = resp_headers.get("Content-Length") or resp_headers.get(
                "content-length"
            )
            if size_header:
                try:
                    metadata["size"] = int(size_header)
                except ValueError:
                    logger.debug("Content-Length 不是有效數字: %s", size_header)

            content_type_header = resp_headers.get("Content-Type") or resp_headers.get(
                "content-type"
            )
            if content_type_header:
                metadata["content_type"] = content_type_header

            disposition = resp_headers.get("Content-Disposition") or resp_headers.get(
                "content-disposition"
            )
            filename = self._extract_filename_from_disposition(disposition)
            if filename:
                metadata["file_name"] = filename

            return metadata

        try:
            response = requests.head(content_url, headers=headers, timeout=10)

            if response.status_code == 405:
                # 某些 SharePoint 端點不支援 HEAD，改用部分下載
                range_headers = headers.copy()
                range_headers["Range"] = "bytes=0-0"
                response = requests.get(content_url, headers=range_headers, timeout=10)

            response.raise_for_status()

            metadata = _extract_headers(response.headers)
            return metadata if metadata else None

        except requests.exceptions.RequestException as e:
            logger.warning(f"取得檔案 Metadata 失敗: {e}", exc_info=True)
            return None

    def _get_mime_type(self, file_type: str) -> str:
        """
        根據檔案類型字串取得 MIME 類型

        Args:
            file_type: 檔案類型（例如: pdf, docx, xlsx）

        Returns:
            MIME 類型字串
        """
        mime_types = {
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "txt": "text/plain",
            "csv": "text/csv",
            "json": "application/json",
            "xml": "application/xml",
            "zip": "application/zip",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
        }
        return mime_types.get(file_type.lower(), "application/octet-stream")

    def _extract_filename_from_disposition(
        self, disposition: Optional[str]
    ) -> Optional[str]:
        """從 Content-Disposition 標頭解析檔名"""

        if not disposition:
            return None

        match = re.search(
            r"filename\*?=([^;]+)",
            disposition,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        value = match.group(1).strip().strip('"')
        # RFC 5987 編碼的情況 (UTF-8''filename)
        if value.lower().startswith("utf-8''"):
            value = value[7:]

        return unquote(value)
