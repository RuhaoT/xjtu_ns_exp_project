from dataclasses import replace

from domain.authentication_model import AuthResult, Credentials, Session
from domain.http_model import (HTTPLayerInterfaceRequest,
                               HTTPLayerInterfaceResponse, HTTPPayloadType,
                               HTTPResponse, HTTPServerAddress)
from domain.setting_model import DEFAULT_HTTP_REQUEST_TEMPLATE, Setting
from service.http_client import (HttpClientSocket,
                                 handle_common_http_error)


def encode_auth_form(credentials: Credentials) -> tuple[bytes, int]:
    """Encode credentials into a form for authentication, also return the length of content before encoding."""
    try:
        auth_form = {
            "httpd_username": credentials.username,
            "httpd_password": credentials.password,
            "login": "Login",
        }

        auth_form_str = "&".join(
            f"{key}={value}" for key, value in auth_form.items()
        )

        return auth_form_str.encode("utf-8"), len(auth_form_str)
    except Exception as e:
        raise ValueError(f"Error encoding authentication form: {str(e)}")

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, http_client: HttpClientSocket, session_token: str = None):
        self.http_client = http_client
        self.session_token = session_token

    async def login(self, credentials: Credentials, setting: Setting = None) -> AuthResult:
        """Authenticate user with the server."""
        try:
            
            if setting is None:
                setting = replace(Setting())
                setting.http_request_template = DEFAULT_HTTP_REQUEST_TEMPLATE
            
            server_info = HTTPServerAddress(
                host_ip=credentials.server_address,
                port=80,
            )
            auth_request = replace(setting.http_request_template)
            auth_request.url = setting.auth_service_url
            auth_request.method = "POST"
            auth_request.server_connection = server_info
            auth_request.payload_type = HTTPPayloadType.FORM_URLENCODED
            auth_request.payload_bytes, auth_request.content_length_before_encoding = encode_auth_form(credentials)
            auth_request.allow_redirects = True
            auth_request.maintain_session_during_redirects = True
            
            response = self.http_client.handle_request(auth_request)
            
            # Check response status
            if response.vaild_response:
                
                if response.http_response.set_cookie != None:
                    # Extract session token from cookies
                    self.session_token = response.http_response.set_cookie
                    return AuthResult(
                        success=True,
                        session_model=Session(session_token=self.session_token, session_server_info=server_info),
                    )
                else:
                    if response.http_response.location == "/login.html":
                        # Authentication failed
                        return AuthResult(
                            success=False,
                            error_message="Authentication failed. Invalid username or password."
                        )
                    else:
                        # check status code
                        error_message = handle_common_http_error(response.http_response.status_code)
                        # in this specific case, if the auth info is invalid, the server will always redirect to the login page, until the maximum number of redirects is reached
                        # TODO: better handle this case
                        if response.http_response.payload_bytes != None:
                            error_message = "Invalid username or password."
                        elif error_message == None:
                            error_message = f"Unknown error occurred, status code: {response.http_response}"
                        else:
                            pass
                            
                        # Authentication failed for another reason
                        return AuthResult(
                            success=False,
                            error_message="Authentication failed." + error_message
                        )
            else:
                # Handle invalid response
                return AuthResult(
                    success=False,
                    error_message="Invalid response from server: " + str(response.error_message)
                )
                
        except Exception as e:
            # Handle network or other errors
            return AuthResult(
                success=False,
                error_message=f"Error during authentication: {str(e)}"
            )
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.session_token is not None