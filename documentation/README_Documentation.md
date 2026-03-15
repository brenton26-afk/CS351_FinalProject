# Here we can store images and other files and .txt files with example steps for a demo.

## Here we should add some tips so that we do not PAY for anything when creating this project:
 - Always close our instances.
 - Be careful about using or avoiding GLUE.
 - Use only t2.micro EC2.
 - Keep S3 under 5GB.

## Steps to upload files to aws bucket
 - Create Bucket with name
 - Go to aws Security Credentials
 - Create Access Key
 - Save Access Key and Secret Access Key
 - Open terminal at file location
 - (Make sure to pip install boto3 if not already done).
 - (aws configure. add in your ACCESS KEY, SECRET_ACCESS_KEY, Region=us-east-2, Output format = json).
 - Make sure file path we are uploading to s3 bucket is written into the local python file.
 - Run update_to_s3.py and hopefully it is successful. Troubleshoot if not.
 - You can now edit a file and run the sync_to_s3.py python file to check if it will update the changed files.
 - We now need to find a way to make this consistant and things like that... like if you update or change or add a file or remove a file the sync file should be running constantly (every second or few) to keep track of changes.
 - Also make sure we think about what we should do with files when files are REMOVED... I think we should keep it in the bucket anyways for a period just incase. or we can create a recycle bin file folder.
