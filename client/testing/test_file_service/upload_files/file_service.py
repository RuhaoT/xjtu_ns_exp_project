# NOTE: DEPRECATED


#!/usr/local/bin/python3.12
import cgi
import os
import sys
import tempfile
import shutil
from datetime import datetime
import subprocess
from dataclasses import dataclass, asdict
from enum import StrEnum
from typing import Optional
import json
import hashlib

# 启用调试
import cgitb
cgitb.enable()

# all models are transferred in JSON format
class FileServerRequestType(StrEnum):
    """Enumeration for file server request types."""
    LIST_FILES = "list_files"
    DOWNLOAD_FILE = "download_file"
    UPLOAD_FILE = "upload_file"

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
    
@dataclass
class FileServerRequestAPI:
    """Model for file server request API. This is the payload for the file server request."""
    request_type: FileServerRequestType = None

@dataclass
class FileServerResponseAPI:
    """Model for file server response API. This is the payload for the file server response."""
    request_success: bool = False
    request_data: Optional[ServerFileList] = None
    error_message: Optional[str] = None

def handle_request() -> FileServerResponseAPI:
    """Handle the file server request."""
    try:
        # for debugging
        # raise ValueError("Debugging enabled")
        
        # Create a form object to handle POST data
        form = cgi.FieldStorage()

        # Check if the request type is provided
        if "request_type" not in form:
            return FileServerResponseAPI(
                request_success=False,
                error_message="No request type provided"
            )

        # Get the request type
        request_type = form["request_type"].value

        # Process the request based on the request type
        if request_type == FileServerRequestType.LIST_FILES:
            return fetch_file_list()
        else:
            raise NotImplementedError(f"Request type '{request_type}' is not implemented.")
    except Exception as e:
        return FileServerResponseAPI(
            request_success=False,
            error_message=str(e)
        )

def send_response(response: FileServerResponseAPI):
    """Send the HTTP response."""
    # turn the response into JSON
    response_json = json.dumps(asdict(response), ensure_ascii=False)
    # let apache handle header
    body = "\n" + response_json
    print(body)
    # flush the output
    sys.stdout.flush()
    # close the output
    sys.stdout.close()
    return

def fetch_file_list() -> FileServerResponseAPI:
    """Fetch the list of files from the server."""
    try:
        # Define the upload directory
        upload_dir = os.path.join(os.path.dirname(__file__), '..')

        # Check if the directory exists
        if not os.path.exists(upload_dir):
            return FileServerResponseAPI(
                request_success=False,
                error_message="Upload directory does not exist"
            )

        # Get the list of files in the directory
        file_list = []
        for file_name in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file_name)
            if os.path.isfile(file_path):
                # Calculate the MD5 hash and get its hexadecimal representation
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                file_list.append(SingleFile(file_name=file_name, file_hash=file_hash))

        # Create the response object
        response = FileServerResponseAPI(
            request_success=True,
            request_data=ServerFileList(valid_list=True, file_list=file_list)
        )

        return response
    except Exception as e:
        # Return error response instead of raising string
        return FileServerResponseAPI(
            request_success=False,
            error_message=f"Error fetching file list: {str(e)}"
        )

if __name__ == "__main__":
    # Handle the request and send the response
    response = handle_request()
    send_response(response)