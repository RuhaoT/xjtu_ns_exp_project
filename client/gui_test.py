from time import monotonic

from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Button, Digits

class TimeDisplay(Digits):
    """Display the stopwatch time."""
    
    start_time = reactive(monotonic)
    time = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(interval=1 / 60, callback=self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.time = monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic() - self.time
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0

class Stopwatch(HorizontalGroup):
    """Stopwatch widget."""
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        time_display = self.query_one(TimeDisplay)
        if event.button.id == "start":
            time_display.start()
            self.add_class("started")
        elif event.button.id == "stop":
            time_display.stop()
            self.remove_class("started")
        elif event.button.id == "reset":
            time_display.reset()
    
    def compose(self) -> ComposeResult:
        """Compose the stopwatch UI."""
        yield TimeDisplay()
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")



class StopwatchApp(App):
    
    
    CSS_PATH = "./stopwatch03.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield Footer()
        yield VerticalScroll(Stopwatch(), Stopwatch(), Stopwatch(), id="timers")
    
    def action_toggle_dark(self) -> None:
        
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    
    def action_add_stopwatch(self) -> None:
    
        new_stopwatch = Stopwatch()
        self.query_one(VerticalScroll).mount(new_stopwatch)
        new_stopwatch.scroll_visible()

    def action_remove_stopwatch(self) -> None:
        """Called to remove a timer."""
        timers = self.query("Stopwatch")
        if timers:
            timers.last().remove()

if __name__ == "__main__":
    app = StopwatchApp()
    app.run()