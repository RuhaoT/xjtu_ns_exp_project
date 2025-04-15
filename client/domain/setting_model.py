from dataclasses import dataclass
from . import http_model

DEFAULT_HTTP_REQUEST_TEMPLATE = http_model.HTTPLayerInterfaceRequest(
    url="",
    method="GET",
    version="HTTP/1.1",
    connection_keep_alive=True,
    cookie=None,
    user_agent="Client by Ruhao Tian",
    accept=None,
    accept_encoding=None,
    timeout=10,
    max_retries=3,
    allow_redirects=True,
    max_redirects=5,
    maintain_session_during_redirects=True,
    content_encoding=None,
    transfer_encoding=None,
    transfer_encoding_chunk_size=1024,
    payload_type=None,
    payload_bytes=None
)

@dataclass
class Setting:
    """Setting model for client configuration."""
    http_request_template: http_model.HTTPLayerInterfaceRequest = None
    
    auth_service_url: str = "/login"
    file_service_url: str = "/file_service"
    
    local_file_dir: str = "./local_files/"
    # upload_file_dir: str = "./non-exist_dir"