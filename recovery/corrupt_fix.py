print("This file attempts to repair corrupted files returned by corruption_scanner.py")

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter


TEXT_EXTENSIONS = {
    ".txt", ".log", ".md", ".csv", ".json", ".xml", ".html", ".htm"
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"
}

PDF_EXTENSIONS = {
    ".pdf"
}


def run_corruption_scanner(folder_path: str) -> list[str]:
    """
    Runs corruption_scanner.py and returns a list of corrupted file paths.
    """
    scanner_path = Path(__file__).with_name("corruption_scanner.py")

    if not scanner_path.exists():
        print(f"Error: Could not find {scanner_path}")
        return []

    try:
        result = subprocess.run(
            [sys.executable, str(scanner_path), folder_path],
            capture_output=True,
            text=True
        )
    except Exception as e:
        print(f"Error running corruption_scanner.py: {e}")
        return []

    output_lines = result.stdout.splitlines()
    corrupted_files = []

    collecting = False
    for line in output_lines:
        line = line.strip()

        if line == "Corrupted files found:":
            collecting = True
            continue

        if collecting and line:
            corrupted_files.append(line)

    return corrupted_files


def make_backup(file_path: str) -> str:
    """
    Makes a .bak backup before attempting repair.
    """
    backup_path = file_path + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path


def try_repair_text_file(file_path: str) -> bool:
    """
    Tries to repair text-like files by reading with replacement for bad bytes
    and rewriting as clean UTF-8.
    """
    ext = Path(file_path).suffix.lower()

    try:
        make_backup(file_path)

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if ext == ".json":
            try:
                obj = json.loads(content)
                repaired_content = json.dumps(obj, indent=4)
            except Exception:
                return False
        else:
            repaired_content = content

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            f.write(repaired_content)

        return True
    except Exception:
        return False


def try_repair_image_file(file_path: str) -> bool:
    """
    Tries to repair image files by opening and re-saving them.
    """
    try:
        make_backup(file_path)

        with Image.open(file_path) as img:
            img.load()

            temp_path = file_path + ".repaired"
            img.save(temp_path)

        os.replace(temp_path, file_path)
        return True
    except Exception:
        temp_path = file_path + ".repaired"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False


def try_repair_pdf_file(file_path: str) -> bool:
    """
    Tries to repair a PDF by reading pages and writing a new PDF.
    """
    try:
        make_backup(file_path)

        temp_path = file_path + ".repaired"

        with open(file_path, "rb") as infile:
            reader = PdfReader(infile)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            with open(temp_path, "wb") as outfile:
                writer.write(outfile)

        os.replace(temp_path, file_path)
        return True
    except Exception:
        temp_path = file_path + ".repaired"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False


def try_repair_file(file_path: str) -> bool:
    """
    Chooses the correct repair attempt based on file extension.
    """
    ext = Path(file_path).suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return try_repair_text_file(file_path)

    if ext in IMAGE_EXTENSIONS:
        return try_repair_image_file(file_path)

    if ext in PDF_EXTENSIONS:
        return try_repair_pdf_file(file_path)

    print(f"Skipping unsupported file type: {file_path}")
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: py corrupt_fix.py \"C:\\path\\to\\folder\"")
        return 2

    folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"Error: Folder does not exist: {folder_path}")
        return 2

    corrupted_files = run_corruption_scanner(folder_path)

    if not corrupted_files:
        print("No corrupted files to repair.")
        return 0

    print("Files marked as corrupted:")
    for file_path in corrupted_files:
        print(file_path)

    print("\nAttempting repairs...\n")

    repaired = []
    failed = []

    for file_path in corrupted_files:
        print(f"Trying to repair: {file_path}")

        if try_repair_file(file_path):
            print(f"SUCCESS: Repaired {file_path}\n")
            repaired.append(file_path)
        else:
            print(f"FAILED: Could not repair {file_path}\n")
            failed.append(file_path)

    print("Repair summary:")
    print(f"Successfully repaired: {len(repaired)}")
    print(f"Failed to repair: {len(failed)}")

    if repaired:
        print("\nRepaired files:")
        for file_path in repaired:
            print(file_path)

    if failed:
        print("\nFiles that could not be repaired:")
        for file_path in failed:
            print(file_path)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())