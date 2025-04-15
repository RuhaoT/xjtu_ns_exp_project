"""Data models for the client domain."""

from dataclasses import dataclass
from typing import Optional
from enum import StrEnum
from .http_model import HTTPServerAddress

@dataclass
class Credentials:
    """User credentials model."""
    server_address: str
    username: str
    password: str

@dataclass
class Session:
    """User session model."""
    session_token: str = None
    session_server_info: HTTPServerAddress = None
    # user_name: str


@dataclass
class AuthResult:
    """Authentication result model."""
    success: bool
    session_model: Optional[Session] = None
    error_message: Optional[str] = None
