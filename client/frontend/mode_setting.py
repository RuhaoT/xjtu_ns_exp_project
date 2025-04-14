from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid, Vertical, VerticalScroll, HorizontalGroup
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Static, Input, SelectionList, Switch
from textual.widgets.selection_list import Selection
from frontend.utils import HeaderBar

class SwitchableSetting(HorizontalGroup):
    
    def __init__(self, label: str, value: str, id: str, classes: str):
        super().__init__(id=id, classes=classes)
        self.label = label
        self.value = value
    
    def compose(self) -> ComposeResult:
        """Compose the switchable setting with a label and a switch."""
        yield Static(self.label, classes="setting-label")
        yield Switch(id=f"{self.id}-switch", value=self.value == "on", classes="setting-switch")
    

class SettingsScreen(Screen):
    """A settings screen with a simple text placeholder."""

    def __init__(self):
        super().__init__()
        self.settings_text = "Settings Screen"

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""

        # header & footer
        yield HeaderBar("Test", "Client Settings")
        yield Footer()

        yield Static("Settings Screen", classes="settings-screen")
        yield Button("Save", classes="settings-button", id="save-button")
        yield Button("Cancel", classes="settings-button", id="cancel-button")
        
        # Create a vertical scroll container for settings
        yield VerticalScroll(SwitchableSetting("Enable Notifications", "on", "notifications", "setting-item"),
            SwitchableSetting("Dark Mode", "off", "dark-mode", "setting-item"),
            SwitchableSetting("Auto Save", "on", "auto-save", "setting-item"),
            SwitchableSetting("Show Line Numbers", "off", "line-numbers", "setting-item"),
            SwitchableSetting("Enable Sounds", "on", "sounds", "setting-item"),
            SwitchableSetting("Language", "English", "language", "setting-item"),
        )
            

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        pass