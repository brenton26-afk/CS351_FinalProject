# A part of the Backup folder

print("Hello World!")
import os
import boto3
from botocore.exceptions import ClientError

LOCAL_FOLDER = r"C:\Users\bover\Downloads\CS 351\Final Project\projectData"
BUCKET_NAME = "cs351-storage-bucket-project-demo"
S3_PREFIX = "backups/"

def upload_file(s3_client, local_file_path, bucket_name, s3_key):
    #upload a file to s3.
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f"Failed to upload {local_file_path}: {e}")
    except ClientError as e:
        print(f"Failed to upload {local_file_path}: {e}")

def upload_folder_to_s3(local_folder, bucket_name, s3_prefix=""):
    # go thru a local folder and upload all files to s3.
    s3_client = boto3.client("s3")

    if not os.path.exists(local_folder):
        print(f"Error: folder '{local_folder}' does not exist.")
        return
    
    for root, dirs, files in os.walk(local_folder):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)

            #build relative path so folder structure is preserved is s3
            relative_path = os.path.relpath(local_file_path, local_folder)
            s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")
            
            upload_file(s3_client, local_file_path, bucket_name, s3_key)


if __name__ == "__main__":
    upload_folder_to_s3(LOCAL_FOLDER, BUCKET_NAME, S3_PREFIX)