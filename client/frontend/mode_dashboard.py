from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Static, Input, SelectionList
from textual.widgets.selection_list import Selection
from frontend.utils import HeaderBar

class FileSelector(Container):
    """A simple file selector widget."""
    
    

    def compose(self) -> ComposeResult:
        """Compose the file selector widget."""

        yield SelectionList[str](
            Selection("Test File 1", 1),
            Selection("Test File 2", 2, True),
            Selection("Test File 3", 3),
            id="file-selector",
        )

    def on_mount(self) -> None:
        """Called when the widget is mounted to the screen."""

        self.query_one(SelectionList).border_title = "File Selector"


class OperationPanel(Container):
    """A simple operation panel with buttons for actions."""

    def compose(self) -> ComposeResult:
        """Compose the operation panel with buttons."""
        yield Button("Download", id="open-button", classes="operation-button")
        yield Button("Upload", id="save-button", classes="operation-button")
        yield Button("View", id="close-button", classes="operation-button")
        yield Button("Refresh", id="refresh-button", classes="operation-button")

class DashboardScreen(Screen):
    """A simple dashboard screen with a placeholder text."""

    def __init__(self):
        super().__init__()
        self.dashboard_text = "Dashboard Screen"

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen."""

        # header & footer
        yield HeaderBar("Test", "Client Dashboard")

        with Horizontal(id="dashboard-main-component"):

            # file selector
            yield FileSelector()

            with Vertical(id="dashboard-content"):
                yield OperationPanel(
                    id="operation-panel-2",
                )

        yield Footer()