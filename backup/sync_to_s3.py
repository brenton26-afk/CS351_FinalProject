import os
import sys
import hashlib
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


S3_PREFIX = "backups/"


def normalize_prefix(prefix: str) -> str:
    prefix = prefix.strip().replace("\\", "/").strip("/")
    return f"{prefix}/" if prefix else ""


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


def compute_file_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def build_s3_key(local_file_path: str, local_folder: str, s3_prefix: str) -> str:
    relative_path = os.path.relpath(local_file_path, local_folder)
    relative_path = relative_path.replace("\\", "/")
    return f"{normalize_prefix(s3_prefix)}{relative_path}"


def build_local_path_from_key(s3_key: str, local_folder: str, s3_prefix: str) -> str:
    prefix = normalize_prefix(s3_prefix)

    if prefix and s3_key.startswith(prefix):
        relative_path = s3_key[len(prefix):]
    else:
        relative_path = s3_key

    relative_path = relative_path.replace("/", os.sep)
    return os.path.join(local_folder, relative_path)


def get_remote_object_info(s3_client, bucket_name: str, s3_key: str):
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        metadata = response.get("Metadata", {})
        return {
            "exists": True,
            "size": response["ContentLength"],
            "filehash": metadata.get("filehash")
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["404", "NoSuchKey", "NotFound"]:
            return {
                "exists": False,
                "size": None,
                "filehash": None
            }
        raise


def upload_file(s3_client, local_file_path: str, bucket_name: str, s3_key: str) -> None:
    file_hash = compute_file_sha256(local_file_path)

    try:
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={
                "Metadata": {
                    "filehash": file_hash
                }
            }
        )
        print(f"Uploaded: {local_file_path} -> s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"Failed to upload {local_file_path}: {e}")
        raise


def sync_local_files_to_s3(s3_client, local_folder: str, bucket_name: str, s3_prefix: str) -> None:
    if not os.path.isdir(local_folder):
        raise FileNotFoundError(f"Folder does not exist: {local_folder}")

    for root, _, files in os.walk(local_folder):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)

            if should_skip_file(local_file_path):
                continue

            s3_key = build_s3_key(local_file_path, local_folder, s3_prefix)
            remote_info = get_remote_object_info(s3_client, bucket_name, s3_key)

            if not remote_info["exists"]:
                print(f"New file found: {local_file_path}")
                upload_file(s3_client, local_file_path, bucket_name, s3_key)
                continue

            local_size = os.path.getsize(local_file_path)
            local_hash = compute_file_sha256(local_file_path)

            remote_hash = remote_info["filehash"]
            remote_size = remote_info["size"]

            changed = False

            if remote_hash:
                changed = (local_hash != remote_hash)
            else:
                changed = (local_size != remote_size)

            if changed:
                print(f"Changed file found: {local_file_path}")
                upload_file(s3_client, local_file_path, bucket_name, s3_key)
            else:
                print(f"Unchanged, skipping: {local_file_path}")


def download_missing_local_files_from_s3(s3_client, local_folder: str, bucket_name: str, s3_prefix: str) -> None:
    paginator = s3_client.get_paginator("list_objects_v2")
    prefix = normalize_prefix(s3_prefix)

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            s3_key = obj["Key"]

            if s3_key.endswith("/"):
                continue

            local_file_path = build_local_path_from_key(s3_key, local_folder, s3_prefix)

            if should_skip_file(local_file_path):
                continue

            if not os.path.exists(local_file_path):
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                print(f"Missing local file found. Restoring from S3: {local_file_path}")
                s3_client.download_file(bucket_name, s3_key, local_file_path)


def cleanup_old_versions(s3_client, bucket_name: str, s3_prefix: str, keep_versions: int = 2) -> None:
    paginator = s3_client.get_paginator("list_object_versions")
    prefix = normalize_prefix(s3_prefix)

    versions_by_key = {}
    delete_markers_by_key = {}

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for version in page.get("Versions", []):
            key = version["Key"]
            versions_by_key.setdefault(key, []).append(version)

        for marker in page.get("DeleteMarkers", []):
            key = marker["Key"]
            delete_markers_by_key.setdefault(key, []).append(marker)

    for key, versions in versions_by_key.items():
        versions.sort(key=lambda v: v["LastModified"], reverse=True)

        versions_to_delete = versions[keep_versions:]

        for version in versions_to_delete:
            version_id = version["VersionId"]
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=version_id)
                print(f"Deleted old version: s3://{bucket_name}/{key} (VersionId={version_id})")
            except ClientError as e:
                print(f"Failed to delete old version for {key}: {e}")

    for key, markers in delete_markers_by_key.items():
        for marker in markers:
            version_id = marker["VersionId"]
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=version_id)
                print(f"Deleted delete marker: s3://{bucket_name}/{key} (VersionId={version_id})")
            except ClientError as e:
                print(f"Failed to delete delete marker for {key}: {e}")


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: py sync_to_s3.py "<bucket_name>" "<folder_path>" [s3_prefix]')
        return 2

    bucket_name = sys.argv[1]
    local_folder = sys.argv[2]
    s3_prefix = sys.argv[3] if len(sys.argv) > 3 else S3_PREFIX

    try:
        s3_client = boto3.client("s3")

        sync_local_files_to_s3(s3_client, local_folder, bucket_name, s3_prefix)
        download_missing_local_files_from_s3(s3_client, local_folder, bucket_name, s3_prefix)
        cleanup_old_versions(s3_client, bucket_name, s3_prefix, keep_versions=2)

        print("Sync complete.")
        return 0

    except Exception as e:
        print(f"Sync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())