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

class ClientApp(App):
    """Main application class for the client."""

    CSS_PATH = "client.tcss"  # Path to the CSS file

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
    session_token = reactive(None, init=False, always_update=True)
    
    def __init__(self):
        super().__init__()
        self.http_client = HttpClientSocket()
        self.auth_service = AuthService(self.http_client)

    def on_mount(self) -> None:
        """The default screen is the dashboard."""
        self.switch_mode("dashboard")


if __name__ == "__main__":
    app = ClientApp()
    app.run()
