# This is one of the files in the recovery part of this project
print("This file scans files for corruption and should return a list (if any) of files.")

import sys
import os
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PyPDF2 import PdfReader


TEXT_EXTENSIONS = {
    ".txt", ".log", ".md", ".csv", ".json", ".xml", ".html", ".htm"
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"
}

PDF_EXTENSIONS = {
    ".pdf"
}


def should_skip_file(file_path: str) -> bool:
    name = os.path.basename(file_path).lower()

    skip_suffixes = (
        ".bak",
        ".repaired",
        ".pre_s3_restore.bak",
        ".tmp",
        ".temp"
    )

    if name.endswith(skip_suffixes):
        return True

    return False


def is_text_file_corrupted(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if ext == ".json":
            json.loads(content)

        return False
    except Exception:
        return True


def is_image_file_corrupted(file_path: str) -> bool:
    try:
        with Image.open(file_path) as img:
            img.verify()
        return False
    except (UnidentifiedImageError, OSError, SyntaxError, Exception):
        return True


def is_pdf_file_corrupted(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            _ = len(reader.pages)
        return False
    except Exception:
        return True


def is_file_corrupted(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return is_text_file_corrupted(file_path)

    if ext in IMAGE_EXTENSIONS:
        return is_image_file_corrupted(file_path)

    if ext in PDF_EXTENSIONS:
        return is_pdf_file_corrupted(file_path)

    return False


def find_corrupted_files(folder_path: str) -> list[str]:
    corrupted_files = []

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            full_path = os.path.join(root, file_name)

            if should_skip_file(full_path):
                continue

            if is_file_corrupted(full_path):
                corrupted_files.append(full_path)

    return corrupted_files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: py corruption_scanner.py "C:\\path\\to\\folder"')
        sys.exit(2)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: Folder does not exist: {folder}")
        sys.exit(2)

    bad_files = find_corrupted_files(folder)

    if bad_files:
        print("Corrupted files found:")
        for file_path in bad_files:
            print(file_path)
        sys.exit(1)
    else:
        print("No corrupted files found.")
        sys.exit(0)