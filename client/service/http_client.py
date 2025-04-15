import gzip
import json
import re
import select
import socket
import time
import urllib.parse
import zlib
from base64 import b64encode
from typing import Any, Dict, Optional, Tuple

from domain.http_model import (HTTPConnectionConfigurations,
                               HTTPContentEncoding,
                               HTTPLayerDecodingModuleInterface,
                               HTTPLayerEncodingModuleInterface,
                               HTTPLayerInterfaceRequest,
                               HTTPLayerInterfaceResponse,
                               HTTPLayerTransmissionModuleInterface,
                               HTTPMethod, HTTPPayloadType, HTTPResponse,
                               HTTPServerAddress, HTTPTransferEncoding)


def handle_common_http_error(status_code: int) -> str:
    """Handle common HTTP errors and return a user-friendly message."""
    error_messages = {
        400: "400 Bad Request: The server could not understand the request.",
        401: "401 Unauthorized: Authentication is required.",
        403: "403 Forbidden: You do not have permission to access this resource.",
        404: "404 Not Found: The requested resource could not be found.",
        500: "500 Internal Server Error: The server encountered an error.",
        502: "502 Bad Gateway: The server received an invalid response from the upstream server.",
        503: "503 Service Unavailable: The server is currently unable to handle the request.",
    }
    return error_messages.get(status_code, None)

def parse_http_url(url: str) -> str:
    """Parse the HTTP URL and return the server address."""
    safe_or_reserved_characters = re.compile(r'[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]')
    
    percent_encoded = re.compile(r'%[0-9A-Fa-f]{2}')
    
    already_encoded = False
    has_unsafe_characters = False
    
    # start parsing
    index = 0
    result = ""
    while index < len(url):
        if percent_encoded.match(url[index:index+3]):
            already_encoded = True
            result += url[index:index+3]
            index += 3
        elif safe_or_reserved_characters.match(url[index]):
            result += url[index]
            index += 1
        else:
            has_unsafe_characters = True
            unsafe_bytes = url[index].encode('utf-8')
            for i in unsafe_bytes:
                result += f"%{i:02X}"
            index += 1
    if has_unsafe_characters and already_encoded:
        raise ValueError("URL contains unsafe characters and already encoded characters, please check the URL")
    return result

def get_http_main_content_type(content_type: str) -> str:
    """Get the main content type from the content type string."""
    if content_type:
        return content_type.split(';')[0].strip()
    return None

# class HttpClient:
#     """HTTP client for making requests to the server."""
    
#     def __init__(self):
#         self.client = httpx.AsyncClient()
#         self.cookies = {}
    
#     async def get(self, url: str, headers: Optional[Dict[str, str]] = None, auth: Tuple[str, str] = None) -> httpx.Response:
#         """Make a GET request."""
#         return await self.client.get(url, auth=auth)
    
#     async def post(self, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None, auth: Tuple[str,str] = None) -> httpx.Response:
#         """Make a POST request."""
        
#         if headers is None:
#             headers = {}
        
#         if auth:
#             # If auth is provided, set the Authorization header for Basic Auth
#             auth_header = f"Basic {b64encode(f'{auth[0]}:{auth[1]}'.encode()).decode()}"
#             headers['Authorization'] = auth_header
        
#         # If data is provided, send it as JSON
#         if data is not None:
#             headers['Content-Type'] = 'application/json'
#             response = await self.client.post(url, json=data, headers=headers, cookies=self.cookies)
#         else:
#             # If no data is provided, send an empty POST request
#             headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        
#         response = await self.client.post(url, headers=headers, cookies=self.cookies)
        
#         # Store cookies for session management
#         if response.cookies:
#             self.cookies.update(response.cookies)
            
#         return response
    
#     async def close(self):
#         """Close the HTTP client."""
#         await self.client.aclose()

class HttpClientSocket:
    """HTTP client with low-level implementation for socket communication."""
    # TODO: HTTPS support
    # TODO: Keep-alive support
    # for now use stateless connection
    
    def __init__(self):
        # support single connection keep-alive for now
        # TODO: connection pool
        self.persistent_socket = None
        self.current_server: HTTPServerAddress = None
        self.socket_timeout = 5  # seconds
    
    def handle_request(self, layer_request_interface: HTTPLayerInterfaceRequest) -> HTTPLayerInterfaceResponse:
        """Handle the HTTP request and return the response, including redirection handling."""
        try:
            # get redirection demands
            allow_redirects = layer_request_interface.allow_redirects
            max_redirects = layer_request_interface.max_redirects
            maintain_session_during_redirects = layer_request_interface.maintain_session_during_redirects
            last_cookie = layer_request_interface.cookie

            # get the first response
            response = self.handle_single_request(layer_request_interface)

            # check if redirection is needed
            if not response.vaild_response:
                # if response is not valid, return the error message
                return response
            elif response.http_response.status_code not in [301, 302, 303, 307, 308]:
                # no redirection needed
                return response

            # if redirection is needed, check if allowed
            if not allow_redirects:
                response.vaild_response = False
                response.error_message = "Redirection is needed, but not allowed"
                return response

            # start redirection loop
            redirect_count = 0
            while redirect_count < max_redirects:
                # check if redirection is needed
                if response.http_response.location:
                    # get the new URL
                    new_url = response.http_response.location
                    print(f"Redirecting to: {new_url}")

                    # create a new request interface
                    layer_request_interface.url = new_url
                    
                    # if maintain_session_during redirects is enabled, copy the session cookies
                    if maintain_session_during_redirects:
                        # if the response has set-cookie header, update the cookies
                        if response.http_response.set_cookie != None:
                            print(f"Updating cookies: {response.http_response.set_cookie}")
                            last_cookie = response.http_response.set_cookie
                            layer_request_interface.cookie = last_cookie

                    # handle the new request
                    response = self.handle_single_request(layer_request_interface)

                    # check if redirection is needed
                    if not response.vaild_response:
                        response.error_message = f"Error during redirection: {response.error_message}"
                        return response

                    redirect_count += 1
                else:
                    # this guarantees that the response is 1. valid and 2. not a redirection
                    # but before returning, apply the last cookie
                    if (not response.http_response.set_cookie) and (last_cookie is not None) and (layer_request_interface.maintain_session_during_redirects):
                        print(f"Applying last cookie: {last_cookie}")
                        response.http_response.set_cookie = last_cookie
                    
                    # return the response
                    return response

            # if max redirects reached, return the response
            response.vaild_response = False
            response.error_message = f"Max redirect count reached: {max_redirects}"
            return response
        except Exception as e:
            print(f"Error handling request: {e}")
            return HTTPLayerInterfaceResponse(
                http_response=None,
                vaild_response=False,
                error_message="Error handling request: " + str(e)
            )
        
    def handle_single_request(self, layer_request_interface: HTTPLayerInterfaceRequest) -> HTTPLayerInterfaceResponse:
        """Handle a single HTTP request and return the response without performing redirection."""
        # Encode the request
        try:
            request_interface = HTTPLayerEncodingModuleInterface(
                url=layer_request_interface.url,
                method=layer_request_interface.method,
                host=layer_request_interface.server_connection.host_ip,
                version=layer_request_interface.version,
                connection_keep_alive=layer_request_interface.connection_keep_alive,
                cookie=layer_request_interface.cookie,
                user_agent=layer_request_interface.user_agent,
                accept=layer_request_interface.accept,
                accept_encoding=layer_request_interface.accept_encoding,
                content_encoding=layer_request_interface.content_encoding,
                content_length_before_encoding=layer_request_interface.content_length_before_encoding,
                transfer_encoding=layer_request_interface.transfer_encoding,
                transfer_encoding_chunk_size=layer_request_interface.transfer_encoding_chunk_size,
                payload_type=layer_request_interface.payload_type,
                payload_bytes=layer_request_interface.payload_bytes,
            )
            encoded_request = self._encode_request(request_interface)
        except ValueError as e:
            print(f"Error encoding request: {e}")
            return HTTPLayerInterfaceResponse(
                http_response=None,
                vaild_response=False,
                error_message="Error encoding request:" + str(e)
            )

        # Create a transmission interface and send the request
        try:
            transmission_interface = HTTPLayerTransmissionModuleInterface(
                encoded_request=encoded_request,
                timeout=layer_request_interface.timeout,
                max_retries=layer_request_interface.max_retries,
                server=layer_request_interface.server_connection,
            )
            response = self._transmit_request(transmission_interface)
        except TimeoutError as e:
            print(f"Error sending request: {e}")
            return HTTPLayerInterfaceResponse(
                http_response=None,
                vaild_response=False,
                error_message="Error sending request: " + str(e)
            )
        except Exception as e:
            print(f"Unexpected error: {e}")
            return HTTPLayerInterfaceResponse(
                http_response=None,
                vaild_response=False,
                error_message="Unexpected error: " + str(e)
            )
        
        # Decode the response
        try:
            decoded_response = self._decode_response(HTTPLayerDecodingModuleInterface(
                response_raw_data=response,))
        except Exception as e:
            print(f"Error decoding response: {e}")
            return HTTPLayerInterfaceResponse(
                http_response=None,
                vaild_response=False,
                error_message="Error decoding response: " + str(e)
            )
        return HTTPLayerInterfaceResponse(
            http_response=decoded_response,
            vaild_response=True,
            error_message=None
        )
    
    def _encode_request(self, encoding_interface: HTTPLayerEncodingModuleInterface) -> bytes:
        """Encode the HTTP request to bytes."""
        # parse the URL
        parsed_url = parse_http_url(encoding_interface.url)
        
        
        request_line = f"{encoding_interface.method} {parsed_url} {encoding_interface.version}\r\n"
        headers = f"Host: {encoding_interface.host}\r\n"
        body_bytes_pretransfer = None # payload before applying transfer encoding
        body_content_encoded = None # payload after applying content encoding
        body_transfer_encoded = None # payload after applying transfer encoding
        content_length = 0
        has_payload = False
        
        if encoding_interface.connection_keep_alive:
            headers += "Connection: keep-alive\r\n"
        else:
            headers += "Connection: close\r\n"

        if encoding_interface.cookie:
            headers += f"Cookie: {encoding_interface.cookie}\r\n"
        
        if encoding_interface.user_agent:
            headers += f"User-Agent: {encoding_interface.user_agent}\r\n"
        
        if encoding_interface.accept:
            headers += f"Accept: {encoding_interface.accept}\r\n"
            
        if encoding_interface.accept_encoding:
            headers += f"Accept-Encoding: {encoding_interface.accept_encoding}\r\n"

        if encoding_interface.payload_type != None:
            has_payload = True
            headers += f"Content-Type: {encoding_interface.payload_type}\r\n"
            
            # Encode payload data
            if encoding_interface.payload_bytes == None:
                raise ValueError("Payload data is required for non-empty payload type")
            

            # DEPRECATED: use encoding_interface.payload_bytes directly
            # NOTE: it is the responsibility of the caller to encode the payload data
            # match encoding_interface.payload_type:
            #     case HTTPPayloadType.JSON:
            #         body_pretransfer = json.dumps(encoding_interface.payload_bytes)
            #     case HTTPPayloadType.FORM:
            #         body_pretransfer = urllib.parse.urlencode(encoding_interface.payload_bytes)
            #     case HTTPPayloadType.TEXT_PLAIN:
            #         body_pretransfer = encoding_interface.payload_bytes
            #     case _:
            #         raise ValueError("Unsupported payload type")
            body_bytes_pretransfer = encoding_interface.payload_bytes
            
            content_length = encoding_interface.content_length_before_encoding
            
            # Apply content encoding
            if encoding_interface.content_encoding != None:
                headers += f"Content-Encoding: {encoding_interface.content_encoding}\r\n"
                match encoding_interface.content_encoding:
                    case HTTPContentEncoding.GZIP:
                        print("Applying content encoding: gzip")
                        body_content_encoded = gzip.compress(body_bytes_pretransfer)
                    case HTTPContentEncoding.DEFLATE:
                        # TODO: deflate encoding
                        raise NotImplementedError("Deflate encoding is not implemented yet")
                    case HTTPContentEncoding.IDENTITY:
                        print("Applying content encoding: identity")
                        # No encoding applied
                        body_content_encoded = body_bytes_pretransfer
                    case _:
                        raise ValueError(f"Unsupported content encoding: {encoding_interface.content_encoding}")
                
                # update content length
                content_length = len(body_content_encoded)
            else:
                # no content encoding applied
                body_content_encoded = body_bytes_pretransfer
            
            # Apply transfer encoding
            if encoding_interface.transfer_encoding != None:
                print(f"Applying transfer encoding: {encoding_interface.transfer_encoding}")
                
                headers += f"Transfer-Encoding: {encoding_interface.transfer_encoding}\r\n"
                
                match encoding_interface.transfer_encoding:
                    case HTTPTransferEncoding.IDENTITY:
                        # No encoding applied
                        body_transfer_encoded = body_content_encoded
                    case HTTPTransferEncoding.CHUNKED:
                        # Apply chunked transfer encoding
                        body_transfer_encoded = self._apply_chunked_transfer_encoding(body_content_encoded, max_chunk_size=encoding_interface.transfer_encoding_chunk_size)
                    case _:
                        raise ValueError(f"Unsupported transfer encoding: {encoding_interface.transfer_encoding}")
                    # TODO: at least add chunked
                
                # update content length
                content_length = len(body_transfer_encoded)
            else:
                # No transfer encoding applied
                body_transfer_encoded = body_content_encoded
            
            # Add content length header
            headers += f"Content-Length: {content_length}\r\n"
        
        # wrapping up the request
        headers += "\r\n"
        # combine request line, headers and body
        request = request_line + headers
        
        if body_bytes_pretransfer:
            print(request+body_bytes_pretransfer.decode())
        else:
            print(request)
        
        header_bytes = request.encode()
        if has_payload:
            request_bytes = header_bytes + body_transfer_encoded
        else:
            request_bytes = header_bytes
        return request_bytes
    
    def _apply_chunked_transfer_encoding(self, data: bytes, max_chunk_size: int = 4096) -> bytes:
        """Apply chunked transfer encoding to the data."""
        
        # check chunk size and data length
        if max_chunk_size <= 0:
            raise ValueError("Chunk size must be greater than 0")
        if len(data) == 0:
            raise ValueError("Data length must be greater than 0")
        
        print(f"Applying chunked transfer encoding with max chunk size: {max_chunk_size}")
        
        # apply chunked transfer encoding
        chunked_data = b''
        data_length = len(data)
        offset = 0
        while offset < data_length:
            chunk_size = min(max_chunk_size, data_length - offset)
            chunk = data[offset:offset + chunk_size]
            chunked_data += f"{chunk_size:x}\r\n".encode() + chunk + b"\r\n"
            offset += chunk_size
        
        # add the final chunk
        chunked_data += b"0\r\n\r\n"
        return chunked_data
    
    def _decode_chunked_transfer_encoding(self, data: bytes) -> bytes:
        """Decode chunked transfer encoding."""
        decoded_data = b''
        offset = 0
        while offset < len(data):
            # Find the end of the chunk size line
            end_of_chunk_size = data.find(b'\r\n', offset)
            if end_of_chunk_size == -1:
                raise ValueError("Invalid chunked data: missing chunk size end")
            
            # Get the chunk size
            chunk_size_hex = data[offset:end_of_chunk_size]
            chunk_size = int(chunk_size_hex, 16)
            offset = end_of_chunk_size + 2
            
            # If chunk size is 0, break the loop
            if chunk_size == 0:
                break
            
            # Get the chunk data
            chunk_data = data[offset:offset + chunk_size]
            decoded_data += chunk_data
            
            # Move to the next chunk
            offset += chunk_size + 2
        
        return decoded_data
    
    def _check_persistent_socket(self, transmission_interface: HTTPLayerTransmissionModuleInterface) -> bool:
        """Check if the persistent socket is still valid."""
        if self.persistent_socket is None:
            return False
        elif self.current_server != transmission_interface.server:
            return False

        try:
            self.persistent_socket.getpeername()
            return True
        except (socket.error, AttributeError):
            return False
    
    def _send_request(self, transmission_interface: HTTPLayerTransmissionModuleInterface) -> socket.socket:
        """Send the HTTP request and return the socket."""
        # if not using keep-alive, create a new socket connection
        # TODO: error handling
        max_retries = transmission_interface.max_retries
        successful_transmission = False
        current_retry = 0
        last_error = "Please check max_retries"
        while current_retry < max_retries and not successful_transmission:
            try:
        
                if transmission_interface.keep_alive == False:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.socket_timeout)
                    sock.connect((transmission_interface.server.host_ip, transmission_interface.server.port))  # Assuming HTTP on port 80
                else:
                    # check persistent socket
                    if not self._check_persistent_socket(transmission_interface):
                        # create a new socket connection
                        self.persistent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.persistent_socket.settimeout(self.socket_timeout)
                        self.persistent_socket.connect((transmission_interface.server.host_ip, transmission_interface.server.port))
                    sock = self.persistent_socket
                    self.current_server = transmission_interface.server
        
                # Send the encoded request
                sock.sendall(transmission_interface.encoded_request)
                successful_transmission = True
            except Exception as e:
                print(f"Error sending request: {e}")
                last_error = str(e)
                current_retry += 1
                if sock:
                    # socket policy: once failed, always reset the current socket
                    sock.close()
                    sock = None
                    if transmission_interface.keep_alive:
                        self.persistent_socket = None
                        self.current_server = None
        if not successful_transmission:
            raise TimeoutError(f"Failed to send after {max_retries} retries, \n last error: {last_error}")
        
        return sock
    
    def _transmit_request(self, transmission_interface: HTTPLayerTransmissionModuleInterface) -> bytes:
        """Send the HTTP request and receive the response."""
                
        # send the request
        sock = self._send_request(transmission_interface)
        
        # Receive the response
        sock.setblocking(False)  # 非阻塞模式
        data = b''
        header_complete = False
        content_length = 0
        body_start_pos = 0

        # 设置合理的总超时时间
        total_timeout = transmission_interface.timeout
        start_time = time.time()

        while time.time() - start_time < total_timeout:
            try:
                # 使用很短的轮询间隔，不会显著延迟处理
                ready = select.select([sock], [], [], 0.1)  # 100ms超时
                if ready[0]:
                    chunk = sock.recv(4096)
                    if not chunk:  # 连接关闭
                        # 如果已经接收到完整头部的GET请求，可以返回了
                        if header_complete and b'GET' in data[:data.find(b'\r\n')]:
                            return data
                        break
                    
                    data += chunk

                    # 如果还没解析头部，检查是否已经接收到完整头部
                    if not header_complete and b'\r\n\r\n' in data:
                        header_complete = True
                        body_start_pos = data.find(b'\r\n\r\n') + 4

                        # 解析Content-Length
                        for line in data[:body_start_pos].split(b'\r\n'):
                            if line.lower().startswith(b'content-length:'):
                                content_length = int(line.split(b':', 1)[1].strip())
                                break
                            
                        # 如果是GET请求且没有Content-Length，可能已经完成
                        if b'GET' in data[:data.find(b'\r\n')] and content_length == 0:
                            return data

                    # 检查是否已经接收到全部数据
                    if header_complete and len(data) - body_start_pos >= content_length:
                        return data

                # 如果没有更多数据但头部已完成，可以检查请求类型
                elif header_complete:
                    if b'GET' in data[:data.find(b'\r\n')] or len(data) - body_start_pos >=     content_length:
                        return data

            except BlockingIOError:
                # 非阻塞模式下没有数据可读会抛出异常
                pass

        # 超时处理
        raise TimeoutError("HTTP request reception timed out")

    def _decode_response(self, response_interface: HTTPLayerDecodingModuleInterface) -> HTTPResponse:
        """Decode the HTTP response from bytes and produce a response object for the upper layer."""
        raw_response = response_interface.response_raw_data
        decoded_response = HTTPResponse()
        body_after_transfer_decoded = None
        body_after_content_decoded = None

        # step 1: separate header and body
        header_end = raw_response.find(b'\r\n\r\n')
        if header_end == -1:
            raise ValueError("Invalid HTTP response format: missing header end")
        header = raw_response[:header_end]
        body = raw_response[header_end + 4:]
        
        # step 2: parse header
        header_lines = header.split(b'\r\n')
        status_line = header_lines[0].decode()
        status_parts = status_line.split(' ')
        decoded_response.version = status_parts[0]
        decoded_response.status_code = int(status_parts[1])
        status_message = ' '.join(status_parts[2:])
        for line in header_lines[1:]:
            key, value = line.decode().split(': ', 1)
            match key:
                case 'Transfer-Encoding':
                    decoded_response.transfer_encoding = value
                case 'Content-Encoding':
                    decoded_response.content_encoding = value
                case 'Content-Length':
                    decoded_response.content_length = int(value)
                case 'Set-Cookie':
                    print(f"Cookie received: {value}")
                    decoded_response.set_cookie = value
                case 'Last-Modified':
                    decoded_response.last_modified = value
                case 'Location':
                    decoded_response.location = value
                case 'Content-Type':
                    decoded_response.content_type = get_http_main_content_type(value)
                case 'Connection':
                    if value.lower() == 'keep-alive':
                        decoded_response.connection_keep_alive = True
                    else:
                        decoded_response.connection_keep_alive = False
                case _:
                    # Ignore other headers
                    pass
        
        # step 3: decode body
        
        if len(body) > 0:
            # first decode transfer encoding
            if decoded_response.transfer_encoding != None:
                match decoded_response.transfer_encoding:
                    case HTTPTransferEncoding.IDENTITY:
                        body_after_transfer_decoded = body
                    case HTTPTransferEncoding.CHUNKED:
                        print("Decoding chunked transfer encoding")
                        body_after_transfer_decoded = self._decode_chunked_transfer_encoding(body)
                    case _:
                        raise ValueError(f"Unsupported transfer encoding: {decoded_response.transfer_encoding}")
                    # TODO: add chunked transfer encoding support
            else:
                body_after_transfer_decoded = body
            
            # then decode content encoding
            if decoded_response.content_encoding != None:
                print(f"Decoding content with encoding: {decoded_response.content_encoding}")
                match decoded_response.content_encoding:
                    case 'gzip':
                        body_after_content_decoded = gzip.decompress(body_after_transfer_decoded)
                    case 'deflate':
                        body_after_content_decoded = zlib.decompress(body_after_transfer_decoded)
                    case 'identity':
                        body_after_content_decoded = body_after_transfer_decoded
                    case _:
                        raise ValueError("Unsupported content encoding")
            else:
                body_after_content_decoded = body_after_transfer_decoded
                
            # NOTE: we don't perform the final decoding as the body might be binary data
                
            # finally set the payload data
            decoded_response.payload_bytes = body_after_content_decoded
            print("--"*10)
            print(f"Decoded response payload: {decoded_response.payload_bytes.decode()}")
            print("--"*10)
        else:
            decoded_response.payload_bytes = None

        return decoded_response