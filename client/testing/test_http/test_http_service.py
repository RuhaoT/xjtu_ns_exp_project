import pytest
from service.http_client import HttpClientSocket
from domain.http_model import HTTPLayerInterfaceRequest, HTTPLayerInterfaceResponse, HTTPServerAddress, HTTPPayloadType, HTTPTransferEncoding, HTTPContentEncoding
from service.authentication import encode_auth_form
from domain.authentication_model import Credentials, AuthResult
from httpx import Response
import yaml
import itertools

def load_test_data(file_path: str):
    """Load test data from a YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def load_login_test_data(test_data):
    """Load login test data from the YAML file."""
    credentials = Credentials(
        server_address="",
        username=test_data['payload_data']['httpd_username'],
        password=test_data['payload_data']['httpd_password'],
    )
    encoded_bytes, content_length_before_encoding = encode_auth_form(credentials)
    print(f"Encoded bytes: {encoded_bytes.decode('utf-8')}")
    return encoded_bytes, content_length_before_encoding

def fetch_http_request_data(yaml_data: dict):
    """Fetch HTTP request data from the loaded YAML data."""
    return HTTPLayerInterfaceRequest(
        url=yaml_data['url'],
        method=yaml_data['method'],
        version=yaml_data['version'],
        server_connection=HTTPServerAddress(
            host_ip=yaml_data['server_connection']['host_ip'],
            port=yaml_data['server_connection']['port']
        ),
        connection_keep_alive=yaml_data['connection_keep_alive'],
        max_retries=yaml_data['max_retries'],
        cookie=yaml_data['cookie'],
        user_agent=yaml_data['user_agent'],
        accept=yaml_data['accept'],
        accept_encoding=yaml_data['accept_encoding'],
        timeout=yaml_data['timeout'],
        transfer_encoding=yaml_data['transfer_encoding'],
        transfer_encoding_chunk_size=yaml_data['transfer_encoding_chunk_size'],
        content_encoding=yaml_data['content_encoding'],
        payload_type=yaml_data['payload_type'],
        payload_bytes=yaml_data['payload_data'],
        allow_redirects=yaml_data['allow_redirects'],
        max_redirects=yaml_data['max_redirects'],
        maintain_session_during_redirects=yaml_data['maintain_session_during_redirects'],
    )

def test_http_client_socket_minimal():
    """Test the HttpClientSocket class."""
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_minimal']
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    http_request = fetch_http_request_data(test_data)

    # Call the handle_request method and check the response
    response = client_socket.handle_request(http_request)
    
    assert isinstance(response, HTTPLayerInterfaceResponse)
    assert response.vaild_response == test_data['expected_response']['valid_response']
    assert response.http_response.status_code == test_data['expected_response']['status_code']

def test_http_client_socket_form_login():
    """Test the HttpClientSocket class."""
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_form_login']
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    http_request = fetch_http_request_data(test_data)
    http_request.payload_bytes, http_request.content_length_before_encoding = load_login_test_data(test_data)

    # Call the handle_request method and check the response
    response = client_socket.handle_request(http_request)
    
    assert isinstance(response, HTTPLayerInterfaceResponse)
    assert response.vaild_response == test_data['expected_response']['valid_response']
    assert response.http_response.status_code == test_data['expected_response']['status_code']
    assert response.http_response.location == test_data['expected_response']['location']
    assert response.http_response.set_cookie != None
    assert response.error_message == test_data['expected_response']['error_message']

def test_http_client_socket_form_login_send_encoding():
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_form_login_send_encoding']
    
    transfer_encodings: list[HTTPTransferEncoding] = test_data['transfer_encoding']
    content_encodings: list[HTTPContentEncoding] = test_data['content_encoding']
    
    encoding_combinations = list(itertools.product(transfer_encodings, content_encodings))
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    for encoding in encoding_combinations:
        transfer_encoding, content_encoding = encoding
        http_request = fetch_http_request_data(test_data)
        http_request.transfer_encoding = transfer_encoding
        http_request.content_encoding = content_encoding
        http_request.payload_bytes, http_request.content_length_before_encoding = load_login_test_data(test_data)
        
        # Call the handle_request method and check the response
        response = client_socket.handle_request(http_request)
        
        assert isinstance(response, HTTPLayerInterfaceResponse)
        assert response.vaild_response == test_data['expected_response']['valid_response']
        assert response.http_response.status_code == test_data['expected_response']['status_code']
        assert response.http_response.location == test_data['expected_response']['location']
        assert response.http_response.set_cookie != None
        assert response.error_message == test_data['expected_response']['error_message']

def test_http_client_socket_minimal_respond_encoding():
    
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_minimal_respond_encoding']
    
    accept_encodings: list[HTTPContentEncoding] = test_data['accept_encoding']
    
    # initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    for encoding in accept_encodings:
        http_request = fetch_http_request_data(test_data)
        http_request.accept_encoding = encoding
        
        # Call the handle_request method and check the response
        response = client_socket.handle_request(http_request)
        
        assert isinstance(response, HTTPLayerInterfaceResponse)
        assert response.vaild_response == test_data['expected_response']['valid_response']
        assert response.http_response.status_code == test_data['expected_response']['status_code']

def test_http_client_socket_form_login_with_redirection():
    """Test the HttpClientSocket class."""
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_form_login_with_redirection']
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    http_request = fetch_http_request_data(test_data)
    http_request.payload_bytes, http_request.content_length_before_encoding = load_login_test_data(test_data)

    # Call the handle_request method and check the response
    response = client_socket.handle_request(http_request)
    
    assert isinstance(response, HTTPLayerInterfaceResponse)
    assert response.vaild_response == test_data['expected_response']['valid_response']
    assert response.http_response.status_code == test_data['expected_response']['status_code']
    assert response.error_message == test_data['expected_response']['error_message']
    assert response.http_response.set_cookie != None

def test_http_client_socket_form_login_with_redirection_respond_infinite():
    """Test the HttpClientSocket class."""
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_form_login_with_redirection_infinite']
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    http_request = fetch_http_request_data(test_data)
    http_request.payload_bytes, http_request.content_length_before_encoding = load_login_test_data(test_data)

    # Call the handle_request method and check the response
    response = client_socket.handle_request(http_request)
    
    assert isinstance(response, HTTPLayerInterfaceResponse)
    assert response.vaild_response == test_data['expected_response']['valid_response']
    assert response.error_message == test_data['expected_response']['error_message']

def test_http_client_socket_parse_url():
    """Test the URL parsing functionality of HttpClientSocket."""
    # Load test data
    test_data = load_test_data('./testing/test_http/test_http_cases.yaml')
    test_data = test_data['test_http_request_parse_url']
    
    # Initialize the HttpClientSocket
    client_socket = HttpClientSocket()
    
    # Test data for HTTP request
    http_request = fetch_http_request_data(test_data)

    # Call the handle_request method and check the response
    response = client_socket.handle_request(http_request)
    
    assert isinstance(response, HTTPLayerInterfaceResponse)
    assert response.vaild_response == test_data['expected_response']['valid_response']
    assert response.http_response.status_code == test_data['expected_response']['status_code']
