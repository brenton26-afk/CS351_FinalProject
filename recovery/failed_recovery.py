print("This file attempts to restore corrupted files from S3 object versions.")

import sys
import os
import shutil
import subprocess
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


DEFAULT_S3_PREFIX = "backups/"


def normalize_prefix(prefix: str) -> str:
    prefix = prefix.strip().replace("\\", "/").strip("/")
    return f"{prefix}/" if prefix else ""


def run_corruption_scanner(folder_path: str) -> list[str]:
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
    backup_path = file_path + ".pre_s3_restore.bak"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
    return backup_path


def build_s3_key(file_path: str, folder_path: str, s3_prefix: str) -> str:
    relative_path = os.path.relpath(file_path, folder_path).replace("\\", "/")
    return f"{normalize_prefix(s3_prefix)}{relative_path}"


def get_all_versions_for_key(s3_client, bucket_name: str, object_key: str) -> list[dict]:
    paginator = s3_client.get_paginator("list_object_versions")
    versions = []

    for page in paginator.paginate(Bucket=bucket_name, Prefix=object_key):
        for version in page.get("Versions", []):
            if version.get("Key") == object_key:
                versions.append(version)

    versions.sort(key=lambda v: v["LastModified"], reverse=True)
    return versions


def get_restore_version_id(s3_client, bucket_name: str, object_key: str) -> str | None:
    versions = get_all_versions_for_key(s3_client, bucket_name, object_key)

    if not versions:
        print(f"No versions found in bucket for key: {object_key}")
        return None

    if len(versions) >= 2:
        return versions[1]["VersionId"]

    print(f"Only one version exists for {object_key}. Falling back to latest version.")
    return versions[0]["VersionId"]


def restore_version_to_local_file(s3_client, bucket_name: str, object_key: str, local_file_path: str) -> bool:
    version_id = get_restore_version_id(s3_client, bucket_name, object_key)

    if not version_id:
        return False

    try:
        make_backup(local_file_path)

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=object_key,
            VersionId=version_id
        )

        with open(local_file_path, "wb") as f:
            f.write(response["Body"].read())

        print(f"Restored file: {local_file_path}")
        print(f"Bucket: {bucket_name}")
        print(f"Key: {object_key}")
        print(f"VersionId used: {version_id}")
        return True

    except ClientError as e:
        print(f"Error restoring {object_key} from S3: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error restoring {local_file_path}: {e}")
        return False


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: py failed_recovery.py "<folder_path>" "<bucket_name>" [s3_prefix]')
        return 2

    folder_path = sys.argv[1]
    bucket_name = sys.argv[2]
    s3_prefix = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_S3_PREFIX

    if not os.path.isdir(folder_path):
        print(f"Error: Folder does not exist: {folder_path}")
        return 2

    s3_client = boto3.client("s3")
    corrupted_files = run_corruption_scanner(folder_path)

    if not corrupted_files:
        print("No corrupted files found. Nothing to restore from S3.")
        return 0

    print("Files still corrupted after local repair attempts:")
    for file_path in corrupted_files:
        print(file_path)

    print("\nAttempting S3 version restore...\n")

    restored = []
    failed = []

    for file_path in corrupted_files:
        object_key = build_s3_key(file_path, folder_path, s3_prefix)

        print(f"Trying S3 restore for: {file_path}")
        print(f"Using S3 key: {object_key}")

        if restore_version_to_local_file(s3_client, bucket_name, object_key, file_path):
            restored.append(file_path)
            print()
        else:
            failed.append(file_path)
            print()

    print("S3 restore summary:")
    print(f"Restored from S3: {len(restored)}")
    print(f"Could not restore: {len(failed)}")

    if restored:
        print("\nFiles restored from S3:")
        for file_path in restored:
            print(file_path)

    if failed:
        print("\nFiles that could not be restored from S3:")
        for file_path in failed:
            print(file_path)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())