import pytest
from service.http_client import HttpClientSocket
from service.authentication import AuthService
from domain.http_model import HTTPLayerInterfaceRequest, HTTPLayerInterfaceResponse, HTTPServerAddress, HTTPPayloadType, HTTPTransferEncoding, HTTPContentEncoding
from domain.authentication_model import Credentials, AuthResult
from httpx import Response
import yaml
import itertools
import asyncio

def load_test_data(file_path: str):
    """Load test data from a YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def test_auth_login_minimal():
    """Test the AuthService login method with minimal data."""
    
    #load test data
    test_data = load_test_data('./testing/test_auth/test_auth_cases.yaml')
    test_data = test_data['test_auth_login_minimal']
    
    test_credentials = Credentials(
        server_address=test_data['credentials']['server_address'],
        username=test_data['credentials']['username'],
        password=test_data['credentials']['password']
    )
    
    # initialize the AuthService
    http_client = HttpClientSocket()
    auth_service = AuthService(http_client)
    response = asyncio.run(auth_service.login(test_credentials))
    print(response.error_message)
    assert response.success == test_data['expected']['success']
    assert response.session_model.session_token != None