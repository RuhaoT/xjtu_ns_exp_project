from dataclasses import replace

from domain.authentication_model import AuthResult, Credentials
from frontend.utils import DynamicText, HeaderBar
from service.authentication import AuthService
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, Footer, Header, Input, SelectionList,
                             Static)
from textual.widgets.selection_list import Selection


class LoginScreen(Screen):
    """A login widget. For now use static text as a placeholder.

    Should be placed in the center of the screen, with three input fields:
    - Server address
    - Username
    - Password
    And two buttons:
    - Login
    - Cancel
    """

    def __init__(self):
        super().__init__()
        self.server_address = "Server Address"
        self.username = "Username"
        self.password = "Password"



    def compose(self) -> ComposeResult:
        """Compose the login widget."""
        yield HeaderBar("XJTU NETWORK LAB 2025 CLIENT SERVER", "Client Login")
        with Vertical(id="login-screen-outer-vertical"):

            # main login component
            yield Static("Server Address", id="server-address")
            self.server_input = Input(placeholder="Enter server address", id="server-input")
            yield self.server_input
            
            yield Static("Username", id="username")
            self.username_input = Input(placeholder="Enter username", id="username-input")
            yield self.username_input
            
            yield Static("Password", id="password")
            self.password_input = Input(placeholder="Enter password", password=False, id="password-input")
            yield self.password_input
            
            self.login_status = DynamicText(id="login-status")
            self.login_status.text = "Not logged in"
            yield self.login_status
            
            # login and cancel buttons
            with Horizontal(classes="button-container"):
                yield Button("Login", id="login-button", classes="login-button")
                yield Button("Logout", id="logout-button", classes="logout-button")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "login-button":
            
            # Retrieve input values
            server_address = self.server_input.value.strip()
            username = self.username_input.value.strip()
            password = self.password_input.value.strip()
            if not server_address:
                self.login_status.text = "Please fill in the server address."
                return
            
            credential = Credentials(
                server_address=server_address,
                username=username,
                password=password
            )
            
            # update login status
            self.login_status.text = "Logging in..."
            
            # Perform login operation
            auth_service: AuthService = self.app.auth_service
            result = await auth_service.login(credential, setting=self.app.current_setting)
            if result.success:
                self.add_class("logged-in")
                # update current session
                self.app.current_session = replace(result.session_model)
                self.login_status.text = f"Login successful, got session: \n{self.app.current_session}"
            else:
                self.login_status.text = "Login failed: " + (result.error_message or "Unknown error")
                return

        elif event.button.id == "logout-button":
            # clear session and remove logged-in class
            self.app.current_session = None
            self.login_status.text = "Not logged in"
            self.remove_class("logged-in")