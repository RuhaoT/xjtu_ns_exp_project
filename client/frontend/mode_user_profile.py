from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Static, Input, SelectionList
from textual.widgets.selection_list import Selection
from frontend.utils import HeaderBar, DynamicText
from domain.authentication_model import Credentials, AuthResult
from textual.reactive import reactive
from service.authentication import AuthService

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
        with Vertical():
            yield HeaderBar("Test", "Client Login")

            # main login component
            yield Static("Server Address")
            self.server_input = Input(placeholder="Enter server address", id="server-input")
            yield self.server_input
            
            yield Static("Username")
            self.username_input = Input(placeholder="Enter username", id="username-input")
            yield self.username_input
            
            yield Static("Password")
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
            result = await auth_service.login(credential)
            if result.success:
                self.add_class("logged-in")
                # self.app.session_token = result.session_token
                self.login_status.text = "Logged in successfully"
            else:
                self.login_status.text = "Login failed: " + (result.error_message or "Unknown error")
                return

        elif event.button.id == "logout-button":
            # clear session token and remove logged-in class
            self.app.session_token = None
            self.login_status.text = "Not logged in"
            self.remove_class("logged-in")