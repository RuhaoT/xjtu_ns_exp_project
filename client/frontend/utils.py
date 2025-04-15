from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (Button, Footer, Header, Input, SelectionList,
                             Static)
from textual.widgets.selection_list import Selection


class HeaderBar(Static):
    """A custom header bar with content aligned to left and right."""

    def __init__(self, left_text: str, right_text: str):
        super().__init__()
        self.left_text = left_text
        self.right_text = right_text

    def compose(self) -> ComposeResult:
        """Compose the header with left and right aligned text."""
        yield Static(self.left_text, classes="left-aligned")
        yield Static(self.right_text, classes="right-aligned")

class DynamicText(Widget):
    
    text = reactive("Dynamic Text", init=True, always_update=True)
    
    def render(self) -> str:
        """Render the dynamic text."""
        return self.text