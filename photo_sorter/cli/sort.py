import os
import shutil
import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from photo_sorter.utils import get_file_metadata, analyze_disk_usage_by_file_type
import concurrent.futures
import filecmp
from pathlib import Path

app = typer.Typer()
console = Console()

@app.command(
    "run",
    help="Sort photos from a source directory to a destination directory."
)
def sort_photos_command(
    source_dir: Path = typer.Argument(..., help="The source directory containing the photos."),
    dest_dir: Path = typer.Argument(..., help="The destination directory to store the sorted photos."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate the sorting process without copying files."),
    include: list[str] = typer.Option(None, "--include", help="File extensions to include (e.g., .jpg .png)."),
    exclude: list[str] = typer.Option(None, "--exclude", help="File extensions to exclude (e.g., .gif .raw)."),
    map_ext: list[str] = typer.Option(None, "--map-ext", help="Map a file extension to a specific folder (e.g., --map-ext .mov Videos).")
):
    """
    Sorts photos from a source directory to a destination directory.
    """
    if not source_dir.is_dir():
        console.print(f"[bold red]Error: Source directory '{source_dir}' not found.[/bold red]")
        raise typer.Exit(code=1)

    if not dest_dir.is_dir():
        console.print(f"Destination directory '{dest_dir}' not found. Creating it...")
        os.makedirs(dest_dir)

    include_types = [f".{ext.lower().lstrip('.')}" for ext in include] if include else None
    exclude_types = [f".{ext.lower().lstrip('.')}" for ext in exclude] if exclude else None
    
    extension_mapping = {}
    if map_ext:
        for mapping in map_ext:
            ext, folder = mapping.split()
            extension_mapping[f".{ext.lower().lstrip('.')}"] = folder

    sorter = PhotoSorter(source_dir, dest_dir, dry_run, include_types, exclude_types, extension_mapping)
    sorter.sort()

class PhotoSorter:
    def __init__(self, source_dir: Path, dest_dir: Path, dry_run: bool, include_types: list[str], exclude_types: list[str], extension_mapping: dict):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.dry_run = dry_run
        self.include_types = include_types
        self.exclude_types = exclude_types
        self.extension_mapping = extension_mapping
        self.sorted_files = []
        self.errors = []
        self.file_counts = {}
        self.processed_files = 0
        self.skipped_files = []

    def _check_disk_space(self, files_to_process):
        # Filter files based on include/exclude types before calculating total size
        filtered_files = []
        for file_path in files_to_process:
            file_ext = file_path.suffix.lower()
            if self.include_types and file_ext not in self.include_types:
                continue
            if self.exclude_types and file_ext in self.exclude_types:
                continue
            filtered_files.append(file_path)

        total_size = sum(os.path.getsize(file) for file in filtered_files)
        _, _, free_space = shutil.disk_usage(self.dest_dir)
        if total_size > free_space:
            console.print(f"[bold red]Error: Not enough disk space. Required: {total_size / (1024*1024):.2f} MB, Available: {free_space / (1024*1024):.2f} MB")
            raise typer.Exit(code=1)

    def _process_file(self, file_path: Path, progress, task):
        progress.update(task, advance=1)
        console.log(f"Processing {file_path}...")
        file_ext = file_path.suffix.lower()

        if self.include_types and file_ext not in self.include_types:
            return None
        if self.exclude_types and file_ext in self.exclude_types:
            return None

        try:
            self.processed_files += 1
            self.file_counts[file_ext] = self.file_counts.get(file_ext, 0) + 1
            if file_ext in self.extension_mapping:
                dest_path = self.dest_dir / self.extension_mapping[file_ext]
            else:
                metadata = get_file_metadata(file_path)
                creation_date = metadata['original_date'] or metadata['creation_date']
                year = creation_date.strftime("%Y")
                month = creation_date.strftime("%m")
                file_type = metadata['file_type']
                dest_path = self.dest_dir / year / month / file_type
            
            filename = file_path.name
            dest_file_path = dest_path / filename
            
            if dest_file_path.exists():
                if filecmp.cmp(file_path, dest_file_path, shallow=False):
                    self.skipped_files.append((file_path, dest_file_path))
                    return ("skipped", (file_path, dest_file_path))
                else:
                    i = 1
                    while True:
                        name, ext = file_path.stem, file_path.suffix
                        new_filename = f"{name}_{i}{ext}"
                        new_dest_file_path = dest_path / new_filename
                        if not new_dest_file_path.exists():
                            dest_file_path = new_dest_file_path
                            break
                        i += 1

            if not self.dry_run:
                dest_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_file_path)
            
            return ("sorted", (file_path, dest_file_path))

        except Exception as e:
            return ("error", (file_path, str(e)))

    def sort(self):
        with Progress(console=console) as progress:
            files_to_process = [file_path for file_path in self.source_dir.rglob('*') if file_path.is_file()]
            self._check_disk_space(files_to_process)
            task = progress.add_task("[cyan]Sorting...", total=len(files_to_process))

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self._process_file, file_path, progress, task) for file_path in files_to_process]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        if result[0] == "sorted":
                            self.sorted_files.append(result[1])
                        elif result[0] == "skipped":
                            self.skipped_files.append(result[1])
                        elif result[0] == "error":
                            self.errors.append(result[1])

        self.print_summary()

    def print_summary(self):
        console.print("\n[bold green]Sorting Complete![/bold green]")
        console.print(f"Processed {self.processed_files} files.")

        if self.sorted_files:
            table = Table(title="Sorted Files Summary")
            table.add_column("Source", style="cyan")
            table.add_column("Destination", style="magenta")

            for source, dest in self.sorted_files:
                table.add_row(str(source), str(dest))
            
            counts_table = Table(title="File Counts")
            counts_table.add_column("File Type", style="cyan")
            counts_table.add_column("Count", style="magenta")

            for file_type, count in self.file_counts.items():
                counts_table.add_row(file_type, str(count))

            layout = Layout()
            layout.split_row(Panel(table), Panel(counts_table))
            console.print(layout)

        if self.skipped_files:
            skipped_table = Table(title="Skipped Files (Duplicates)")
            skipped_table.add_column("Source", style="cyan")
            skipped_table.add_column("Destination", style="yellow")

            for source, dest in self.skipped_files:
                skipped_table.add_row(str(source), str(dest))

            console.print(skipped_table)

        if self.errors:
            error_table = Table(title="Errors")
            error_table.add_column("File", style="cyan")
            error_table.add_column("Error", style="red")

            for file, error in self.errors:
                error_table.add_row(str(file), error)

            console.print(error_table)


@app.command(
    "disk-usage",
    help="Analyze disk space usage by file type in a directory."
)
def disk_usage_command(
    directory: Path = typer.Argument(..., help="The directory to analyze.")
):
    """
    Analyzes disk space usage by file type and reports it in a table with bars.
    """
    if not directory.is_dir():
        console.print(f"[bold red]Error: Directory '{directory}' not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Analyzing disk usage in '{directory}'...\n[/bold green]")

    try:
        file_type_sizes = analyze_disk_usage_by_file_type(directory)

        if not file_type_sizes:
            console.print("[yellow]No files found or no disk usage to report.[/yellow]")
            return

        total_size_bytes = sum(size for _, size in file_type_sizes)

        table = Table(title="Disk Usage by File Type", show_footer=True)
        table.add_column("File Type", style="cyan", no_wrap=True)
        table.add_column("Size", style="magenta", justify="right")
        table.add_column("Percentage", style="green", justify="right")
        table.add_column("Bar", style="blue", justify="left")

        max_bar_length = 30

        def format_size(size_bytes: int) -> str:
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes / (1024**2):.2f} MB"
            elif size_bytes < 1024**4:
                return f"{size_bytes / (1024**3):.2f} GB"
            else:
                return f"{size_bytes / (1024**4):.2f} TB"

        for file_type, size_bytes in file_type_sizes:
            percentage = (size_bytes / total_size_bytes) * 100 if total_size_bytes > 0 else 0
            bar_length = int((percentage / 100) * max_bar_length)
            bar = "█" * bar_length + "░" * (max_bar_length - bar_length)
            table.add_row(
                file_type,
                format_size(size_bytes),
                f"{percentage:.2f}%",
                bar
            )
        
        table.add_section()
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{format_size(total_size_bytes)}[/bold]",
            "[bold]100.00%[/bold]",
            ""
        )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)
