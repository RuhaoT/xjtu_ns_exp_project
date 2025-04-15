from dataclasses import dataclass
from typing import Optional
from enum import StrEnum
from .http_model import HTTPServerAddress
import sys
import hashlib
from domain.authentication_model import Session
from domain.setting_model import Setting

class FileServerRequestType(StrEnum):
    """Enumeration for file server request types."""
    LIST_FILES = "list_files"
    DOWNLOAD_FILE = "download_file"
    UPLOAD_FILE = "upload_file"
    
class DirectViewFileType(StrEnum):
    """Enumeration for direct view file types."""
    TXT = "txt"
    INI = "ini"
    JSON = "json"
    MARKDOWN = "md"

@dataclass
class SingleFile:
    """Model for a single file."""
    file_name: str = None
    file_hash: Optional[str] = None
    file_data: Optional[bytes] | Optional[str] = None


@dataclass
class ServerFileList:
    """Model for a list of files on the server."""
    valid_list: bool = False
    file_list: list[SingleFile] = None
    error_message: Optional[str] = None

@dataclass
class FetchServerFileInterface:
    """The fetch interface the file service provides to upper layers."""
    current_session: Session = None
    setting: Setting = None

@dataclass
class FileDownloadInterface:
    """The download interface the file service provides to upper layers."""
    file_name_list: list[str] = None
    current_session: Session = None
    setting: Setting = None

@dataclass
class FileDownloadResult:
    """Model for the result of a file download."""
    # note this result don't include file as they've already stored in the file system
    download_success: bool = False
    error_message: Optional[str] = None
    downloaded_file_name_list: list[str] = None

@dataclass
class FileUploadInterface:
    """The upload interface the file service provides to upper layers."""
    file_path_or_file_dir_path: str = None
    current_session: Session = None
    setting: Setting = None

@dataclass
class FileUploadResult:
    """Model for the result of a file upload."""
    upload_success: bool = False
    error_message: Optional[str] = None
    uploaded_file_name_list: list[str] = None
    already_uploaded_file_name_list: Optional[list[str]] = None
    
@dataclass
class FileServerRequestAPI:
    """Model for file server request API. This is the payload for the file server request."""
    request_type: FileServerRequestType = None
    request_download_file_list: Optional[list[SingleFile]] = None
    request_upload_file_list: Optional[list[SingleFile]] = None

@dataclass
class FileServerResponseAPI:
    """Model for file server response API. This is the payload for the file server response."""
    request_success: bool = False
    request_data: Optional[list[SingleFile]] = None
    error_message: Optional[str] = None
