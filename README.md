# Photo Sorter

A command-line tool to organize photos into folders by date and file type.

## Features

*   Sorts photos by year, month, and file type (e.g., `YYYY/MM/JPG`).
*   Copies files to a new destination, leaving the originals untouched.
*   A "dry run" mode to preview changes before copying.
*   Filter files by extension, allowing you to include or exclude specific types.
*   Interactive command-line interface.
*   Robust error handling.

## Usage

```bash
python main.py <source_directory> <destination_directory> [options]
```

### Options

*   `--dry-run`: Preview the changes without copying files.
*   `--include`: A space-separated list of file extensions to include (e.g., `--include .jpg .png`).
*   `--exclude`: A space-separated list of file extensions to exclude (e.g., `--exclude .gif .raw`).

