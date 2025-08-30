import os
import shutil
import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from photo_sorter.utils import get_creation_date
import concurrent.futures
import filecmp

app = typer.Typer()
console = Console()

@app.command(
    "run",
    help="Sort photos from a source directory to a destination directory."
)
def sort_photos_command(
    source_dir: str = typer.Argument(..., help="The source directory containing the photos."),
    dest_dir: str = typer.Argument(..., help="The destination directory to store the sorted photos."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate the sorting process without copying files."),
    include: list[str] = typer.Option(None, "--include", help="File extensions to include (e.g., .jpg .png)."),
    exclude: list[str] = typer.Option(None, "--exclude", help="File extensions to exclude (e.g., .gif .raw)."),
    map_ext: list[str] = typer.Option(None, "--map-ext", help="Map a file extension to a specific folder (e.g., --map-ext .mov Videos).")
):
    """
    Sorts photos from a source directory to a destination directory.
    """
    if not os.path.isdir(source_dir):
        console.print(f"[bold red]Error: Source directory '{source_dir}' not found.[/bold red]")
        raise typer.Exit(code=1)

    if not os.path.isdir(dest_dir):
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
    def __init__(self, source_dir, dest_dir, dry_run, include_types, exclude_types, extension_mapping):
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
        total_size = sum(os.path.getsize(file) for file in files_to_process)
        _, _, free_space = shutil.disk_usage(self.dest_dir)
        if total_size > free_space:
            console.print(f"[bold red]Error: Not enough disk space. Required: {total_size / (1024*1024):.2f} MB, Available: {free_space / (1024*1024):.2f} MB")
            raise typer.Exit(code=1)

    def _process_file(self, file_path, progress, task):
        progress.update(task, advance=1)
        console.log(f"Processing {file_path}...")
        file_ext = os.path.splitext(file_path)[1].lower()

        if self.include_types and file_ext not in self.include_types:
            return None
        if self.exclude_types and file_ext in self.exclude_types:
            return None

        try:
            self.processed_files += 1
            self.file_counts[file_ext] = self.file_counts.get(file_ext, 0) + 1
            if file_ext in self.extension_mapping:
                dest_path = os.path.join(self.dest_dir, self.extension_mapping[file_ext])
            else:
                creation_date = get_creation_date(file_path)
                year = creation_date.strftime("%Y")
                month = creation_date.strftime("%m")
                file_type = file_ext[1:].upper()
                dest_path = os.path.join(self.dest_dir, year, month, file_type)
            
            filename = os.path.basename(file_path)
            dest_file_path = os.path.join(dest_path, filename)
            
            if os.path.exists(dest_file_path):
                if filecmp.cmp(file_path, dest_file_path, shallow=False):
                    self.skipped_files.append((file_path, dest_file_path))
                    return ("skipped", (file_path, dest_file_path))
                else:
                    i = 1
                    while True:
                        name, ext = os.path.splitext(filename)
                        new_filename = f"{name}_{i}{ext}"
                        new_dest_file_path = os.path.join(dest_path, new_filename)
                        if not os.path.exists(new_dest_file_path):
                            dest_file_path = new_dest_file_path
                            break
                        i += 1

            if not self.dry_run:
                os.makedirs(dest_path, exist_ok=True)
                shutil.copy2(file_path, dest_file_path)
            
            return ("sorted", (file_path, dest_file_path))

        except Exception as e:
            return ("error", (file_path, str(e)))

    def sort(self):
        with Progress(console=console) as progress:
            files_to_process = [os.path.join(root, filename) for root, _, files in os.walk(self.source_dir) for filename in files]
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
                table.add_row(source, dest)
            
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
                skipped_table.add_row(source, dest)

            console.print(skipped_table)

        if self.errors:
            error_table = Table(title="Errors")
            error_table.add_column("File", style="cyan")
            error_table.add_column("Error", style="red")

            for file, error in self.errors:
                error_table.add_row(file, error)

            console.print(error_table)
