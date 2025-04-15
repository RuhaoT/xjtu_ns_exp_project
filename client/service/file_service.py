from domain.authentication_model import Credentials, AuthResult, Session
from domain.file_model import (
    ServerFileList,
    SingleFile,
    FileServerRequestAPI,
    FileServerRequestType,
    FileServerResponseAPI,
    FetchServerFileInterface,
    FileDownloadInterface,
    FileUploadInterface,
    FileDownloadResult,
    FileUploadResult,
)
from domain.setting_model import Setting, DEFAULT_HTTP_REQUEST_TEMPLATE
from domain.http_model import (
    HTTPLayerInterfaceRequest,
    HTTPResponse,
    HTTPPayloadType,
    HTTPServerAddress,
    HTTPLayerInterfaceResponse,
)
from service.http_client import HttpClientSocket, handle_common_http_error
import dataclasses
import json
import os
import sys
import hashlib
from dataclasses import replace
import base64


def encode_file_api_to_json(api_request: FileServerRequestAPI) -> tuple[bytes, int]:
    """Encode file API request into a form for server communication, also return the length of content before encoding."""
    try:
        # turn the dataclass to dict, then dump to json
        api_request_dict = dataclasses.asdict(api_request)
        api_request_json_string = json.dumps(api_request_dict)

        # calculate length and encode to bytes
        api_request_bytes = api_request_json_string.encode("utf-8")
        return api_request_bytes, len(api_request_bytes)
    except Exception as e:
        raise ValueError(f"Error encoding file API request: {str(e)}")


class LocalFileBackend:
    """Backend for local file operations."""

    def __init__(self):
        pass

    def load_file(self, file_path: str) -> bytes:
        """Load a file from the local filesystem."""
        try:
            with open(file_path, "rb") as file:
                return file.read()
        except Exception as e:
            raise RuntimeError(f"Error loading file: {str(e)}")

    def save_file(self, file_path: str, data: bytes) -> None:
        """Save data to a file on the local filesystem."""
        try:
            with open(file_path, "wb") as file:
                file.write(data)
        except Exception as e:
            raise RuntimeError(f"Error saving file: {str(e)}")

    def get_working_directory(self) -> str:
        """Get the current working directory."""
        try:
            return os.getcwd()
        except Exception as e:
            raise RuntimeError(f"Error getting working directory: {str(e)}")

    def get_file_hash(self, file_path: str) -> str:
        """Calculate the SHA-256 hash of a file."""
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    md5_hash.update(byte_block)
            return md5_hash.hexdigest()
        except Exception as e:
            raise RuntimeError(f"Error calculating file hash: {str(e)}")


class FileService:
    """Service for file operations."""

    def __init__(
        self, http_client: HttpClientSocket, local_file_backend: LocalFileBackend
    ):
        self.http_client = http_client
        self.local_file_backend = local_file_backend

    def fetch_server_file_list(
        self, layer_request_interface: FetchServerFileInterface
    ) -> ServerFileList:
        try:
            # get http request template
            setting = layer_request_interface.setting
            current_session = layer_request_interface.current_session

            if setting is None or current_session is None:
                raise RuntimeError(
                    "Setting or current session is None. Have you logged in?"
                )

            request = replace(setting.http_request_template)
            request.url = setting.file_service_url
            request.method = "POST"
            request.server_connection = current_session.session_server_info
            request.cookie = current_session.session_token
            request.payload_type = HTTPPayloadType.JSON
            request.payload_bytes, request.content_length_before_encoding = (
                encode_file_api_to_json(
                    FileServerRequestAPI(request_type=FileServerRequestType.LIST_FILES)
                )
            )
            request.allow_redirects = True
            request.maintain_session_during_redirects = True

            response = self.http_client.handle_request(request)

            # Check response status
            if response.vaild_response:
                if response.http_response.status_code == 200:
                    response_data = json.loads(
                        response.http_response.payload_bytes.decode("utf-8")
                    )
                    if (
                        "request_success" in response_data
                        and response_data["request_success"]
                    ):
                        file_list = ServerFileList(
                            valid_list=True,
                            file_list=[
                                SingleFile(
                                    file_name=file["file_name"],
                                    file_hash=file["file_hash"],
                                )
                                for file in response_data.get("request_data", {})
                            ],
                        )
                        return file_list
                    else:
                        return ServerFileList(
                            valid_list=False,
                            error_message=f"Failed to fetch file list from server: {response_data.get('error_message', 'Unknown error')}",
                        )
                else:
                    # try to handle common http error
                    error_message = handle_common_http_error(
                        response.http_response.status_code
                    )
                    if error_message is None:
                        error_message = "Unknown error"
                    return ServerFileList(
                        valid_list=False,
                        error_message="Failed to fetch file list from server."
                        + error_message,
                    )
            else:
                return ServerFileList(
                    valid_list=False,
                    error_message="Invalid response from server."
                    + response.error_message,
                )
        except Exception as e:
            return ServerFileList(
                valid_list=False,
                error_message=f"Error fetching server file list: {str(e)}",
            )

    def download_file_batch(
        self, layer_request_interface: FileDownloadInterface
    ) -> FileDownloadResult:
        """Download single file or multiple files from the server."""
        try:
            # check if the file name list is empty
            if not layer_request_interface.file_name_list:
                return FileDownloadResult(
                    download_success=False,
                    error_message="No file selected. Nothing to download.",
                )

            # 1. get server file list
            fetch_file_list_request = FetchServerFileInterface(
                current_session=layer_request_interface.current_session,
                setting=layer_request_interface.setting,
            )
            current_server_file_list = self.fetch_server_file_list(
                fetch_file_list_request
            )
            if not current_server_file_list.valid_list:
                raise RuntimeError(
                    "Error fetching server file list before download: "
                    + current_server_file_list.error_message
                )

            # 2. match download file from server file list
            # if not found, raise error

            file_name_list = layer_request_interface.file_name_list
            request_download_file_info_list: list[SingleFile] = []
            for file_name in file_name_list:
                if not any(
                    file.file_name == file_name
                    for file in current_server_file_list.file_list
                ):
                    raise RuntimeError(f"File '{file_name}' not found on server.")
                else:
                    request_download_file_info_list.append(
                        next(
                            file
                            for file in current_server_file_list.file_list
                            if file.file_name == file_name
                        )
                    )

            # 3. cache mechanism: check local file & hash
            # if local file exists and hash matches, skip download
            # if local file exists but hash doesn't match, raise error
            # TODO: more ways to handle file conflict
            actual_download_file_info_list: list[SingleFile] = []
            for file_info in request_download_file_info_list:
                local_file_path = (
                    layer_request_interface.setting.local_file_dir + file_info.file_name
                )
                if os.path.exists(local_file_path):
                    local_file_hash = self.local_file_backend.get_file_hash(
                        local_file_path
                    )
                    if local_file_hash == file_info.file_hash:
                        # skip download
                        continue
                    else:
                        raise RuntimeError(
                            f"Local file '{file_info.file_name}' exists but has hash mismatch."
                        )
                else:
                    # add to download list
                    actual_download_file_info_list.append(file_info)

            # 4. download files
            download_request_body = FileServerRequestAPI(
                request_type=FileServerRequestType.DOWNLOAD_FILE,
                request_download_file_list=actual_download_file_info_list,
            )

            # fetch http request template
            setting = layer_request_interface.setting
            current_session = replace(layer_request_interface.current_session)
            http_request = replace(setting.http_request_template)
            http_request.url = setting.file_service_url
            http_request.method = "POST"
            http_request.server_connection = current_session.session_server_info
            http_request.cookie = current_session.session_token
            http_request.payload_type = HTTPPayloadType.JSON
            http_request.payload_bytes, http_request.content_length_before_encoding = (
                encode_file_api_to_json(download_request_body)
            )
            http_request.allow_redirects = True
            http_request.maintain_session_during_redirects = True
            # handle request
            response = self.http_client.handle_request(http_request)
            # Check response status
            if response.vaild_response:
                if response.http_response.status_code == 200:
                    response_data = json.loads(
                        response.http_response.payload_bytes.decode("utf-8")
                    )
                    if (
                        "request_success" in response_data
                        and response_data["request_success"]
                    ):
                        # save file to local
                        actual_download_file_name_list = []
                        for file_info in actual_download_file_info_list:
                            local_file_path = (
                                layer_request_interface.setting.local_file_dir
                                + file_info.file_name
                            )
                            # find downloaded file in response
                            downloaded_file_list = response_data.get("request_data", [])
                            downloaded_file = next(
                                (
                                    file
                                    for file in downloaded_file_list
                                    if file["file_name"] == file_info.file_name
                                ),
                                None,
                            )
                            if downloaded_file is None:
                                raise RuntimeError(
                                    f"Downloaded file '{file_info.file_name}' not found in response."
                                )

                            # because json cannot serialize bytes, here the file is transferred as to base64 code, then ascii string
                            # so need to decode it to bytes
                            file_bytes_base64 = downloaded_file["file_data"].encode(
                                "ascii"
                            )
                            file_bytes = base64.b64decode(file_bytes_base64)

                            self.local_file_backend.save_file(
                                local_file_path, file_bytes
                            )
                            actual_download_file_name_list.append(file_info.file_name)
                        return FileDownloadResult(
                            download_success=True,
                            downloaded_file_name_list=actual_download_file_name_list,
                        )
                    else:
                        return FileDownloadResult(
                            download_success=False,
                            error_message=f"Failed to download files from server: {response_data.get('error_message', 'Unknown error')}",
                        )
                else:
                    # try to handle common http error
                    error_message = handle_common_http_error(
                        response.http_response.status_code
                    )
                    if error_message is None:
                        error_message = "Unknown error"
                    return FileDownloadResult(
                        download_success=False,
                        error_message="Failed to download files from server."
                        + error_message,
                    )
            else:
                return FileDownloadResult(
                    download_success=False,
                    error_message="Invalid response from server."
                    + response.error_message,
                )
        except Exception as e:
            return FileDownloadResult(
                download_success=False,
                error_message=f"Error downloading files: {str(e)}",
            )

    def upload_file_batch(self, layer_request_interface: FileUploadInterface):
        """Upload single file or multiple files to the server."""
        # this is basically the same as download_file_batch, but upload
        try:
            # check if the file name list is empty
            if not layer_request_interface.file_path_or_file_dir_path:
                return FileUploadResult(
                    upload_success=False,
                    error_message="No file selected. Nothing to upload.",
                )

            # 1. get server file list
            fetch_file_list_request = FetchServerFileInterface(
                current_session=layer_request_interface.current_session,
                setting=layer_request_interface.setting,
            )
            current_server_file_list = self.fetch_server_file_list(
                fetch_file_list_request
            )
            if not current_server_file_list.valid_list:
                raise RuntimeError(
                    "Error fetching server file list before upload: "
                    + current_server_file_list.error_message
                )

            # 2. match upload file from local files
            # if not found, raise error
            # turn the path to absolute path
            file_path_or_file_dir_path = os.path.abspath(
                layer_request_interface.file_path_or_file_dir_path
            )
            # first check if the input is a file or a directory
            if os.path.isfile(file_path_or_file_dir_path):
                # if it's a file, just add it to the list
                file_path_list = [file_path_or_file_dir_path]
            elif os.path.isdir(file_path_or_file_dir_path):
                # if it's a directory, get all files in the directory
                file_path_list = []
                for root, dirs, files in os.walk(file_path_or_file_dir_path):
                    for file in files:
                        file_path_list.append(os.path.join(root, file))
                if len(file_path_list) == 0:
                    raise RuntimeError(
                        f"No files found in directory: {file_path_or_file_dir_path}. Nothing to upload."
                    )
            else:
                raise RuntimeError(
                    f"Not a valid file or directory: {file_path_or_file_dir_path}"
                )

            request_upload_file_info_list: list[SingleFile] = []
            for file_path in file_path_list:
                if not os.path.exists(file_path):
                    raise RuntimeError(f"File not found on local: {file_path}")
                else:
                    # base64 encode the file to ascii string
                    file_bytes = self.local_file_backend.load_file(file_path)
                    file_bytes_base64 = base64.b64encode(file_bytes)
                    file_bytes_ascii = file_bytes_base64.decode("ascii")
                    # get file name(without path and with extension)
                    file_name = os.path.basename(file_path)
                    request_upload_file_info_list.append(
                        SingleFile(
                            file_name=file_name,
                            file_hash=self.local_file_backend.get_file_hash(file_path),
                            file_data=file_bytes_ascii,
                        )
                    )

            # 3. cache mechanism: check server file & hash
            # if server file exists and hash matches, skip upload
            # if server file exists but hash doesn't match, raise error
            # TODO: more ways to handle file conflict
            actual_upload_file_info_list: list[SingleFile] = []
            already_cached_file_name_list = []
            for file_info in request_upload_file_info_list:
                if any(
                    file.file_name == file_info.file_name
                    for file in current_server_file_list.file_list
                ):
                    server_file_info = next(
                        file
                        for file in current_server_file_list.file_list
                        if file.file_name == file_info.file_name
                    )
                    if server_file_info.file_hash == file_info.file_hash:
                        # skip upload
                        already_cached_file_name_list.append(file_info.file_name)
                        continue
                    else:
                        raise RuntimeError(
                            f"Server file '{file_info.file_name}' exists but has hash mismatch."
                        )
                else:
                    # add to upload list
                    actual_upload_file_info_list.append(file_info)

            # 4. upload files
            upload_request_body = FileServerRequestAPI(
                request_type=FileServerRequestType.UPLOAD_FILE,
                request_upload_file_list=actual_upload_file_info_list,
            )
            # fetch http request template
            setting = layer_request_interface.setting
            current_session = replace(layer_request_interface.current_session)
            http_request = replace(setting.http_request_template)
            http_request.url = setting.file_service_url
            http_request.method = "POST"
            http_request.server_connection = current_session.session_server_info
            http_request.cookie = current_session.session_token
            http_request.payload_type = HTTPPayloadType.JSON
            http_request.payload_bytes, http_request.content_length_before_encoding = (
                encode_file_api_to_json(upload_request_body)
            )
            http_request.allow_redirects = True
            http_request.maintain_session_during_redirects = True

            # handle request
            response = self.http_client.handle_request(http_request)
            # Check response status
            if response.vaild_response:
                if response.http_response.status_code == 200:
                    response_data = json.loads(
                        response.http_response.payload_bytes.decode("utf-8")
                    )
                    if (
                        "request_success" in response_data
                        and response_data["request_success"]
                    ):
                        # get uploaded file name list
                        uploaded_file_name_list = []
                        for file_info in response_data.get("request_data", []):
                            uploaded_file_name_list.append(file_info["file_name"])
                        return FileUploadResult(
                            upload_success=True,
                            uploaded_file_name_list=uploaded_file_name_list,
                            already_uploaded_file_name_list=already_cached_file_name_list,
                        )
                    else:
                        return FileUploadResult(
                            upload_success=False,
                            error_message=f"Failed to upload files to server: {response_data.get('error_message', 'Unknown error')}",
                        )
                else:
                    # try to handle common http error
                    error_message = handle_common_http_error(
                        response.http_response.status_code
                    )
                    if error_message is None:
                        error_message = "Unknown error"
                    return FileUploadResult(
                        upload_success=False,
                        error_message="Failed to upload files to server."
                        + error_message,
                    )
            else:
                return FileUploadResult(
                    upload_success=False,
                    error_message="Invalid response from server."
                    + response.error_message,
                )
        except Exception as e:
            return FileUploadResult(
                upload_success=False, error_message=f"Error uploading files: {str(e)}"
            )
    
    
