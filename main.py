import argparse
import os
from sorter import sort_photos

def main():
    """
    The main entry point for the photo sorter CLI.
    """
    parser = argparse.ArgumentParser(description="Sorts photos by date and file type.")
    parser.add_argument("source_dir", help="The source directory containing the photos.")
    parser.add_argument("dest_dir", help="The destination directory to store the sorted photos.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the sorting process without copying files.")
    parser.add_argument("--include", nargs="+", help="A space-separated list of file extensions to include (e.g., .jpg .png). Note that the dot is optional")
    parser.add_argument("--exclude", nargs="+", help="A space-separated list of file extensions to exclude (e.g., .gif .raw). Note that the dot is optional")
    parser.add_argument("--map-ext", nargs=2, action="append", metavar=("EXT", "FOLDER"), help="Map a file extension to a specific folder (e.g., --map-ext .mov Videos).")

    args = parser.parse_args()

    source_dir = args.source_dir
    dest_dir = args.dest_dir

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' not found.")
        return

    if not os.path.isdir(dest_dir):
        print(f"Destination directory '{dest_dir}' not found. Creating it...")
        os.makedirs(dest_dir)

    include_types = [f".{ext.lower().lstrip('.')}" for ext in args.include] if args.include else None
    exclude_types = [f".{ext.lower().lstrip('.')}" for ext in args.exclude] if args.exclude else None
    
    extension_mapping = {f".{ext.lower().lstrip('.')}": folder for ext, folder in args.map_ext} if args.map_ext else {}

    sort_photos(source_dir, dest_dir, args.dry_run, include_types, exclude_types, extension_mapping)

if __name__ == "__main__":
    main()
