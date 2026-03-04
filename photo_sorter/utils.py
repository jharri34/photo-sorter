import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from PIL import Image


def get_file_type(file_path: Path) -> str:
    """
    Determines the type of a file based on its extension.

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The file type (e.g., 'JPG', 'PNG', 'TXT', 'UNKNOWN').
    """
    extension = file_path.suffix.lstrip('.').upper()
    if extension in ['JPG', 'JPEG']:
        return 'JPG'
    elif extension == 'PNG':
        return 'PNG'
    elif extension == 'GIF':
        return 'GIF'
    elif extension == 'BMP':
        return 'BMP'
    elif extension == 'TIFF':
        return 'TIFF'
    elif extension == 'WEBP':
        return 'WEBP'
    elif extension == 'HEIC':
        return 'HEIC'
    elif extension == 'MP4':
        return 'MP4'
    elif extension == 'MOV':
        return 'MOV'
    elif extension == 'AVI':
        return 'AVI'
    elif extension == 'MKV':
        return 'MKV'
    elif extension == 'PDF':
        return 'PDF'
    elif extension == 'DOCX':
        return 'DOCX'
    elif extension == 'XLSX':
        return 'XLSX'
    elif extension == 'PPTX':
        return 'PPTX'
    elif extension == 'TXT':
        return 'TXT'
    elif extension == 'ZIP':
        return 'ZIP'
    elif extension == 'RAR':
        return 'RAR'
    elif extension == '7Z':
        return '7Z'
    else:
        return 'UNKNOWN'


def get_file_metadata(file_path: Path) -> dict:
    """
    Extracts metadata from a file, including creation date and modification date.
    For image files, it attempts to read EXIF data for the original date.

    Args:
        file_path (Path): The path to the file.

    Returns:
        dict: A dictionary containing file metadata.
    """
    stat = file_path.stat()
    creation_timestamp = stat.st_ctime
    modification_timestamp = stat.st_mtime

    creation_date = datetime.fromtimestamp(creation_timestamp)
    modification_date = datetime.fromtimestamp(modification_timestamp)

    original_date: Optional[datetime] = None
    file_type = get_file_type(file_path)

    if file_type in ['JPG', 'JPEG', 'PNG', 'TIFF', 'WEBP', 'HEIC']:
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # 36867 is DateTimeOriginal, 36868 is DateTimeDigitized, 306 is DateTime
                    # Prioritize DateTimeOriginal, then DateTimeDigitized, then DateTime
                    date_str = exif_data.get(36867) or exif_data.get(36868) or exif_data.get(306)
                    if date_str:
                        try:
                            original_date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            pass  # Fallback to creation/modification date if EXIF format is unexpected
        except Exception:
            pass  # Ignore errors if file is not an image or EXIF data is unreadable

    return {
        'creation_date': creation_date,
        'modification_date': modification_date,
        'original_date': original_date,
        'file_type': file_type,
        'size': stat.st_size
    }


def create_directory_if_not_exists(path: Path):
    """
    Creates a directory if it does not already exist.

    Args:
        path (Path): The path to the directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def move_file(source_path: Path, destination_path: Path):
    """
    Moves a file from a source path to a destination path.

    Args:
        source_path (Path): The current path of the file.
        destination_path (Path): The new path for the file.
    """
    os.rename(source_path, destination_path)


def analyze_disk_usage_by_file_type(directory: Path) -> List[Tuple[str, int]]:
    """
    Analyzes disk usage by file type within a given directory and its subdirectories.

    Args:
        directory (Path): The path to the directory to analyze.

    Returns:
        List[Tuple[str, int]]: A list of tuples, where each tuple contains the file type
                                (extension) and the total size in bytes for that type,
                                sorted from largest to smallest.
    """
    if not directory.is_dir():
        raise ValueError(f"Provided path is not a directory: {directory}")

    file_type_sizes: Dict[str, int] = {}

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if file_path.is_file():
                try:
                    file_type = get_file_type(file_path)
                    size = file_path.stat().st_size
                    file_type_sizes[file_type] = file_type_sizes.get(file_type, 0) + size
                except OSError:
                    # Handle cases where file might be inaccessible or broken symlink
                    continue

    # Sort by size in descending order
    sorted_sizes = sorted(file_type_sizes.items(), key=lambda item: item[1], reverse=True)
    return sorted_sizes
