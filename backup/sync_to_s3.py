import os
import boto3
from botocore.exceptions import ClientError

LOCAL_FOLDER = r"C:\Users\bover\Downloads\CS 351\Final Project\projectData"
BUCKET_NAME = "cs351-storage-bucket-project-demo"
S3_PREFIX = "backups/"

def get_s3_file_size(s3_client, bucket_name, s3_key):
    #returns the size of s3 bucket in bytes, if there is none, itll return none

    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        return response["ContentLength"]
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["404", "NoSuchKey", "NotFound"]:
            return None
        else:
            print(f"Error checking s3 Object {s3_key}: e")
            return None
        

def upload_file(s3_client, local_file_path, bucket_name, s3_key):
    # upload one file
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f"Uploaded: {local_file_path} - > s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"Failed to upload {local_file_path}: e")

def sync_folder_to_s3(local_folder, bucket_name, s3_prefix=""):
    # upload only files that are new or have a different size
    s3_client = boto3.client("s3")

    if not os.path.exists(local_folder):
        print(f"Error: folder '{local_folder}' does not exist.")
        return
    
    for root, dirs, files in os.walk(local_folder):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(local_file_path, local_folder)
            s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")

            local_file_size = os.path.getsize(local_file_path)
            s3_file_size = get_s3_file_size(s3_client, bucket_name, s3_key)

            if s3_file_size is None:
                print(f"New file found: {local_file_path}")
                upload_file(s3_client, local_file_path, bucket_name, s3_key)
            elif local_file_size != s3_file_size:
                print(f"Changed file found: {local_file_path}")
                upload_file(s3_client, local_file_path, bucket_name, s3_key)
            else:
                print(f"Unchanged, skipping: {local_file_path}")

if __name__ == "__main__":
    sync_folder_to_s3(LOCAL_FOLDER, BUCKET_NAME, S3_PREFIX)