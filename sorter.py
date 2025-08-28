import os
import shutil
from datetime import datetime
from PIL import Image

def sort_photos(source_dir, dest_dir, dry_run=False, include_types=None, exclude_types=None, extension_mapping=None):
    """
    Sorts photos from a source directory to a destination directory.

    Args:
        source_dir (str): The path to the source directory.
        dest_dir (str): The path to the destination directory.
        dry_run (bool, optional): If True, simulates the sorting process without moving files. Defaults to False.
        include_types (list, optional): A list of file extensions to include. Defaults to None.
        exclude_types (list, optional): A list of file extensions to exclude. Defaults to None.
        extension_mapping (dict, optional): A dictionary mapping file extensions to specific folders. Defaults to None.
    """
    print(f"Starting photo sort from '{source_dir}' to '{dest_dir}'...")
    if dry_run:
        print("Dry run mode enabled. No files will be copied.")

    if extension_mapping is None:
        extension_mapping = {}

    for root, _, files in os.walk(source_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename)[1].lower()

            if include_types and file_ext not in include_types:
                continue
            if exclude_types and file_ext in exclude_types:
                continue

            try:
                if file_ext in extension_mapping:
                    dest_path = os.path.join(dest_dir, extension_mapping[file_ext])
                else:
                    creation_date = get_creation_date(file_path)
                    year = creation_date.strftime("%Y")
                    month = creation_date.strftime("%m")
                    file_type = file_ext[1:].upper()
                    dest_path = os.path.join(dest_dir, year, month, file_type)
                
                if dry_run:
                    print(f"[DRY RUN] Copying '{file_path}' to '{os.path.join(dest_path, filename)}'")
                else:
                    os.makedirs(dest_path, exist_ok=True)
                    shutil.copy2(file_path, os.path.join(dest_path, filename))
                    print(f"Copied '{file_path}' to '{os.path.join(dest_path, filename)}'")

            except Exception as e:
                print(f"Error processing '{file_path}': {e}")

    print("Photo sorting complete.")

def get_creation_date(file_path):
    """
    Gets the creation date of a file.
    For images, it tries to get the 'date taken' from the EXIF data.
    If the EXIF data is not available, it falls back to the file's modification time.

    Args:
        file_path (str): The path to the file.

    Returns:
        datetime: The creation date of the file.
    """
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # EXIF tag for "Date Time Original" is 36867
                date_time_original = exif_data.get(36867)
                if date_time_original:
                    return datetime.strptime(date_time_original, '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass  # Ignore errors when reading EXIF data

    # Fallback to file modification time
    mod_time = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mod_time)
