from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Static, Input, SelectionList
from textual.widgets.selection_list import Selection
from frontend.mode_dashboard import DashboardScreen
from frontend.mode_setting import SettingsScreen
from frontend.mode_user_profile import LoginScreen
from textual.reactive import reactive
from service.http_client import HttpClientSocket
from service.authentication import AuthService
from service.file_service import FileService, LocalFileBackend
from domain.setting_model import Setting, DEFAULT_HTTP_REQUEST_TEMPLATE


class ClientApp(App):
    """Main application class for the client."""

    # CSS_PATH = "client_debug.tcss"  # Path to the CSS file
    CSS_PATH = "client.tcss"

    BINDINGS = [
        ("f3", "switch_mode('login')", "User Profile"),
        ("f2", "switch_mode('settings')", "Settings"),
        ("f1", "switch_mode('dashboard')", "Dashboard"),
        ("ctrl+q", "quit", "Quit"),
    ]

    MODES = {
        "login": LoginScreen,
        "settings": SettingsScreen,
        "dashboard": DashboardScreen,
    }

    # reactive states
    current_session = reactive(None, init=False, always_update=True)
    current_setting = reactive(None, init=False, always_update=True)

    def __init__(self):
        super().__init__()
        self.local_file_backend = LocalFileBackend()
        self.http_client = HttpClientSocket()
        self.auth_service = AuthService(self.http_client)
        self.file_service = FileService(self.http_client, self.local_file_backend)

        self.app.current_setting = Setting()
        self.app.current_setting.http_request_template = DEFAULT_HTTP_REQUEST_TEMPLATE

    def on_mount(self) -> None:
        """The default screen is the dashboard."""
        self.theme = "monokai"
        self.switch_mode("dashboard")


if __name__ == "__main__":
    app = ClientApp()
    app.run()
