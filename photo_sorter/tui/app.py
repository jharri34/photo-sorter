from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button

class PhotoSorterApp(App):
    """A Textual app to sort photos."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Button("Sort Photos", id="sort_button", variant="primary")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
