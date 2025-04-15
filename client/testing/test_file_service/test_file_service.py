import pytest
from service.http_client import HttpClientSocket
from service.authentication import AuthService
from domain.http_model import HTTPLayerInterfaceRequest, HTTPLayerInterfaceResponse, HTTPServerAddress, HTTPPayloadType, HTTPTransferEncoding, HTTPContentEncoding
from domain.authentication_model import Credentials, AuthResult, Session
from domain.setting_model import Setting, DEFAULT_HTTP_REQUEST_TEMPLATE
from domain.file_model import FileServerRequestAPI, FileServerRequestType, FileServerResponseAPI, ServerFileList, SingleFile, FetchServerFileInterface, FileDownloadInterface, FileDownloadResult, FileUploadInterface, FileUploadResult
from service.file_service import FileService, encode_file_api_to_json, LocalFileBackend
from httpx import Response
import yaml
import itertools
import asyncio
import os

def load_test_data(file_path: str):
    """Load test data from a YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def load_credentials(data: dict) -> Credentials:
    """Load credentials from test data."""
    return Credentials(
        server_address=data['server_credentials']['server_address'],
        username=data['server_credentials']['username'],
        password=data['server_credentials']['password'],
    )

def perform_login_and_get_session(credentials: Credentials) -> Session:
    """Perform login and return session."""
    try:
        client_socket = HttpClientSocket()
        auth_service = AuthService(client_socket)
        setting = None  # Assuming default settings are used
        auth_result: AuthResult = asyncio.run(auth_service.login(credentials,   setting))
        if auth_result.success:
            return auth_result.session_model
        raise RuntimeError("Login failed")
    except Exception as e:
        raise RuntimeError(f"Login failed: {str(e)}")

def test_fetch_file_list():
    
    credential = load_credentials(load_test_data("./testing/test_file_service/test_file_service_cases.yaml"))
    session = perform_login_and_get_session(credential)
    print(session)
    assert session is not None
    
    # for debugging
    # session.session_token = None
    
    http_client = HttpClientSocket()
    file_service = FileService(http_client, LocalFileBackend())
    
    request_interface = FetchServerFileInterface(
        current_session=session,
        setting=None,  # Assuming default settings are used
    )
    response = file_service.fetch_server_file_list(request_interface)
    
    print(response.error_message)
    print(response.file_list)
    assert isinstance(response, ServerFileList)
    assert response.valid_list == True

def test_download_all_file():

    credential = load_credentials(load_test_data("./testing/test_file_service/test_file_service_cases.yaml"))
    session = perform_login_and_get_session(credential)
    print(session)
    assert session is not None

    # get file list
    http_client = HttpClientSocket()
    file_service = FileService(http_client, LocalFileBackend())
    
    request_interface = FetchServerFileInterface(
        current_session=session,
        setting=None,  # Assuming default settings are used
    )
    response = file_service.fetch_server_file_list(request_interface)
    
    file_name_list: list[str] = []
    for file in response.file_list:
        file_name_list.append(file.file_name)
        
    setting = Setting()
    setting.http_request_template = DEFAULT_HTTP_REQUEST_TEMPLATE
    setting.local_file_dir = "./testing/test_file_service/downloaded_files/"
    
    # clean up the downloaded files
    for file_name in file_name_list:
        file_path = f"{setting.local_file_dir}/{file_name}"
        if os.path.exists(file_path):
            os.remove(file_path)
    
    request_interface = FileDownloadInterface(
        file_name_list=file_name_list,
        current_session=session,
        setting=setting,  # Assuming default settings are used
    )
    
    response = file_service.download_file_batch(request_interface)
    
    print(response.error_message)
    assert isinstance(response, FileDownloadResult)
    assert response.download_success == True

def test_download_all_with_cache():

    credential = load_credentials(load_test_data("./testing/test_file_service/test_file_service_cases.yaml"))
    session = perform_login_and_get_session(credential)
    print(session)
    assert session is not None

    # get file list
    http_client = HttpClientSocket()
    file_service = FileService(http_client, LocalFileBackend())
    
    request_interface = FetchServerFileInterface(
        current_session=session,
        setting=None,  # Assuming default settings are used
    )
    response = file_service.fetch_server_file_list(request_interface)
    
    file_name_list: list[str] = []
    for file in response.file_list:
        file_name_list.append(file.file_name)
        
    setting = Setting()
    setting.http_request_template = DEFAULT_HTTP_REQUEST_TEMPLATE
    setting.local_file_dir = "./testing/test_file_service/downloaded_files/"
    
    # clean up the downloaded files
    for file_name in file_name_list:
        file_path = f"{setting.local_file_dir}/{file_name}"
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # download all file one time
    test_download_all_file()
    # now all files are downloaded
    
    # download all file again
    request_interface = FileDownloadInterface(
        file_name_list=file_name_list,
        current_session=session,
        setting=setting,  # Assuming default settings are used
    )
    
    response = file_service.download_file_batch(request_interface)
    
    assert isinstance(response, FileDownloadResult)
    assert response.download_success == True
    assert len(response.downloaded_file_name_list) == 0

def test_upload_file():

    credential = load_credentials(load_test_data("./testing/test_file_service/test_file_service_cases.yaml"))
    session = perform_login_and_get_session(credential)
    print(session)
    assert session is not None

    # get file list
    http_client = HttpClientSocket()
    file_service = FileService(http_client, LocalFileBackend())
    
    file_upload_dir = "./testing/test_file_service/upload_files/"
    
    # get all file NAMEs in the upload directory
    file_name_list: list[str] = []
    for file_name in os.listdir(file_upload_dir):
        file_name_list.append(file_name)
    
    setting = Setting()
    setting.http_request_template = DEFAULT_HTTP_REQUEST_TEMPLATE
    setting.upload_file_dir = "./testing/test_file_service/upload_files/"
    setting.local_file_dir = "./testing/test_file_service/downloaded_files/"
    
    request_interface = FileUploadInterface(
        file_name_list=file_name_list,
        current_session=session,
        setting=setting,  # Assuming default settings are used
    )
    
    response = file_service.upload_file_batch(request_interface)
    
    print(response.error_message)
    print(response.uploaded_file_name_list)
    assert isinstance(response, FileUploadResult)
    assert response.upload_success == True