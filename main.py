import typer
from photo_sorter.cli.sort import app as sort_app
from photo_sorter.tui.app import PhotoSorterApp

app = typer.Typer(
    name="photo-sorter",
    help="A CLI tool to sort photos by date and file type.",
    add_completion=False,
)

app.add_typer(sort_app, name="sort")

@app.command(name="interactive", help="Launch the interactive TUI.")
def interactive_command():
    """
    Launch the interactive TUI.
    """
    app = PhotoSorterApp()
    app.run()

if __name__ == "__main__":
    app()