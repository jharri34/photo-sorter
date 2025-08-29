from datetime import datetime
from PIL import Image
import os

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