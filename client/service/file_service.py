from domain.authentication_model import Credentials, AuthResult, Session
from domain.file_model import ServerFileList, SingleFile
from domain.setting_model import Setting, DEFAULT_HTTP_REQUEST_TEMPLATE
from domain.http_model import HTTPLayerInterfaceRequest, HTTPResponse, HTTPPayloadType,HTTPServerAddress, HTTPLayerInterfaceResponse
from service.http_client import HttpClient, HttpClientSocket

class FileService:
    """Service for file operations."""

    def __init__(self, http_client: HttpClientSocket):
        self.http_client = http_client
    
    def fetch_server_file_list(self, current_session: Session, setting: Setting = None) -> ServerFileList:
        