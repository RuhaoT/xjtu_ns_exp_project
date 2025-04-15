#!/usr/local/bin/python3.12
import os
import hashlib
from enum import Enum
from typing import List, Optional, Dict, Any
import json
from dataclasses import dataclass, asdict
from functools import partial
import base64

from flask import Flask, request, jsonify

app = Flask(__name__)

FILE_DIR = os.path.join(os.path.dirname(__file__), "../test_file_service")

# Keep your existing models
class FileServerRequestType(str, Enum):
    LIST_FILES = "list_files"
    DOWNLOAD_FILE = "download_file"
    UPLOAD_FILE = "upload_file"


@dataclass
class SingleFile:
    file_name: str = None
    file_hash: Optional[str] = None
    file_data: Optional[bytes] | Optional[str] = None


@dataclass
class ServerFileList:
    valid_list: bool = False
    file_list: List[SingleFile] = None
    error_message: Optional[str] = None

@dataclass
class FileServerRequestAPI:
    """Model for file server request API. This is the payload for the file server request."""
    request_type: FileServerRequestType = None
    request_download_file_list: Optional[list[SingleFile]] = None
    request_upload_file_list: Optional[list[SingleFile]] = None


@dataclass
class FileServerResponseAPI:
    request_success: bool = False
    request_data: Optional[List[SingleFile]] = None
    error_message: Optional[str] = None


# Helper function to filter None values when converting dataclasses to dict
def filter_none(obj):
    if isinstance(obj, dict):
        return {k: filter_none(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [filter_none(item) for item in obj]
    return obj


@app.route("/", methods=["POST"])
def file_service():
    try:
        request_data = request.get_json()
        if not request_data or "request_type" not in request_data:
            response = FileServerResponseAPI(
                request_success=False, error_message="No request type provided"
            )
            return jsonify(filter_none(asdict(response)))

        request_type = request_data["request_type"]

        if request_type == FileServerRequestType.LIST_FILES:
            return fetch_file_list()
        elif request_type == FileServerRequestType.DOWNLOAD_FILE:
            return download_file(
                request_download_file_list=request_data.get("request_download_file_list", [])
            )
        elif request_type == FileServerRequestType.UPLOAD_FILE:
            return upload_file(
                request_upload_file_list=request_data.get("request_upload_file_list", [])
            )
        else:
            response = FileServerResponseAPI(
                request_success=False,
                error_message=f"Request type '{request_type}' is not implemented",
            )
            return jsonify(filter_none(asdict(response)))

    except Exception as e:
        response = FileServerResponseAPI(request_success=False, error_message=str(e))
        return jsonify(filter_none(asdict(response)))


def fetch_file_list():
    try:
        # Define the upload directory
        upload_dir = os.path.join(os.path.dirname(__file__), FILE_DIR)

        if not os.path.exists(upload_dir):
            response = FileServerResponseAPI(
                request_success=False, error_message="Upload directory does not exist"
            )
            return jsonify(filter_none(asdict(response)))

        file_list = []
        for file_name in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                file_list.append(SingleFile(file_name=file_name, file_hash=file_hash))

        response = FileServerResponseAPI(
            request_success=True,
            request_data=file_list,
        )
        return jsonify(filter_none(asdict(response)))

    except Exception as e:
        response = FileServerResponseAPI(
            request_success=False, error_message=f"Error fetching file list: {str(e)}"
        )
        return jsonify(filter_none(asdict(response)))

def download_file(request_download_file_list: List[dict]):
    try:
        # Define the upload directory
        upload_dir = os.path.join(os.path.dirname(__file__), FILE_DIR)

        if not os.path.exists(upload_dir):
            response = FileServerResponseAPI(
                request_success=False, error_message="Upload directory does not exist"
            )
            return jsonify(filter_none(asdict(response)))

        for file in request_download_file_list:
            file_path = os.path.join(upload_dir, file['file_name'])
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                file['file_data'] = base64.b64encode(file_bytes).decode('ascii')

        response = FileServerResponseAPI(
            request_success=True,
            request_data=request_download_file_list,
        )
        return jsonify(filter_none(asdict(response)))

    except Exception as e:
        response = FileServerResponseAPI(
            request_success=False, error_message=f"Error downloading files: {str(e)}"
        )
        return jsonify(filter_none(asdict(response)))

def upload_file(request_upload_file_list: List[dict]):
    try:
        # Define the upload directory
        upload_dir = os.path.join(os.path.dirname(__file__), FILE_DIR)

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        for file in request_upload_file_list:
            file_name = file['file_name']
            file_data = base64.b64decode(file['file_data'])
            with open(os.path.join(upload_dir, file_name), "wb") as f:
                f.write(file_data)

        response = FileServerResponseAPI(
            request_success=True,
            request_data=request_upload_file_list,
        )
        return jsonify(filter_none(asdict(response)))

    except Exception as e:
        response = FileServerResponseAPI(
            request_success=False, error_message=f"Error uploading files: {str(e)}"
        )
        return jsonify(filter_none(asdict(response)))

if __name__ == "__main__":
    app.run(debug=True)
