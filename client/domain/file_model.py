from dataclasses import dataclass
from typing import Optional
from enum import StrEnum
from .http_model import HTTPServerAddress
import sys
import hashlib

@dataclass
class SingleFile:
    """Model for a single file."""
    file_name: str = None
    file_hash: str = None

@dataclass
class ServerFileList:
    """Model for a list of files on the server."""
    valid_list: bool = False
    file_list: list[SingleFile] = None
    error_message: Optional[str] = None