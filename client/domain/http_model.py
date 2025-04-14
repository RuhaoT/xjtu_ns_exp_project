"""Data models for the client domain."""

from dataclasses import dataclass
from typing import Optional
from enum import StrEnum

class HTTPMethod(StrEnum):
    """HTTP methods enumeration."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class HTTPPayloadType(StrEnum):
    """HTTP payload types enumeration."""
    JSON = "application/json"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    XML = "application/xml"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    MULTIPART_FORM = "multipart/form-data"

class HTTPTransferEncoding(StrEnum):
    """HTTP transfer encoding types enumeration."""
    CHUNKED = "chunked"
    IDENTITY = "identity"
    # COMPRESS = "compress" # Deprecated
    # DEFLATE = "deflate"
    # GZIP = "gzip"

class HTTPContentEncoding(StrEnum):
    """HTTP content encoding types enumeration."""
    GZIP = "gzip"
    DEFLATE = "deflate"
    COMPRESS = "compress"
    IDENTITY = "identity"
    
@dataclass
class HTTPServerAddress:
    """HTTP server address model."""
    host_ip: str
    port: int = 80

@dataclass
class HTTPResponse:
    """HTTP response model for receiving data from the server."""
    # all default values are None
    status_code: int = None
    version: str = None
    content_type: str = None
    content_length: int = None
    set_cookie: str = None
    last_modified: str = None
    connection_keep_alive: bool = None
    transfer_encoding: str = None
    content_encoding: str = None
    location: str = None

    payload_bytes: bytes = None

@dataclass
class HTTPLayerInterfaceRequest:
    """A unified Interface for passing a request to the HTTP client.
    
    Mainly include:
    - request content from the upper layer handlers, i.e.: authentication form
    - global configurations previously defined by the user, i.e.: timeout
    """
    
    # request model
    url: str
    method: str
    version: str = "HTTP/1.1"
    
    # server connections
    server_connection: HTTPServerAddress = None
    
    # request options
    connection_keep_alive: bool = True
    cookie: dict = None
    user_agent: str = None
    accept: str = None
    accept_encoding: str = None
    
    # transmission options
    timeout: int = 10
    max_retries: int = 3
    allow_redirects: bool = False
    max_redirects: int = 5
    maintain_session_during_redirects: bool = False
    
    # payload options
    content_length_before_encoding: int = None
    content_encoding: HTTPContentEncoding = None
    transfer_encoding: HTTPTransferEncoding = None
    transfer_encoding_chunk_size: int = 1024
    payload_type: HTTPPayloadType = None
    payload_bytes: bytes = None

@dataclass
class HTTPLayerEncodingModuleInterface:
    """HTTP request model for sending data to the server."""
    url: str
    method: str
    host: str
    version: str = "HTTP/1.1"
    
    # request options
    connection_keep_alive: bool = True
    cookie: dict = None
    user_agent: str = None
    accept: str = None
    accept_encoding: str = None

    # payload
    content_encoding: HTTPContentEncoding = None
    content_length_before_encoding: int = None
    transfer_encoding: HTTPTransferEncoding = None
    transfer_encoding_chunk_size: int = None
    payload_type: HTTPPayloadType = None
    payload_bytes: bytes = None
    
@dataclass
class HTTPLayerTransmissionModuleInterface:
    """HTTP request model for sending data to the server."""
    encoded_request: bytes
    server: HTTPServerAddress
    timeout: int = 10
    # TODO: keep-alive, for now just use stateless connection
    keep_alive: bool = False
    max_retries: int = 3

@dataclass
class HTTPLayerDecodingModuleInterface:
    """HTTP response model for receiving data from the server."""
    response_raw_data: bytes

@dataclass
class HTTPConnectionConfigurations:
    """HTTP connection configurations."""
    server: HTTPServerAddress
    timeout: int = 10
    keep_alive: bool = True

@dataclass
class HTTPLayerInterfaceResponse:
    """A unified Interface for the HTTP client to respond to the upper layer handlers."""
    
    # response model
    http_response: HTTPResponse = None
    
    # error handling
    vaild_response: bool = True
    error_message: str = None