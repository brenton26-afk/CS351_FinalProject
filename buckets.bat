@echo off

:: Local folder path:
set "LOCAL_PATH=C:\Users\bover\Downloads\CS 351\Final Project\projectData"


:: Here we make sure everything needed to scan files for corruption is downloaded
pip install --upgrade pip
pip install pillow PyPDF2

:: Lets create the buckets ============================================================================================
set BUCKET=new-bucket-demo-test-3
::set FOLDER=backups

aws s3 mb s3://%BUCKET%
aws s3api put-bucket-versioning --bucket %BUCKET% --versioning-configuration Status=Enabled


type nul > empty.txt
aws s3 cp empty.txt s3://%BUCKET%/backups/
del empty.txt

set BUCKET2=new-bucket-demo-test-4

aws s3 mb s3://%BUCKET2%
aws s3api put-bucket-versioning --bucket %BUCKET2% --versioning-configuration Status=Enabled


type nul > empty.txt
aws s3 cp empty.txt s3://%BUCKET2%/backups/
del empty.txt

:: Buckets Created! =========================================================================================================

:: This will initialize the buckets while a photographer begins editing his photos.
py update_to_s3.py "%BUCKET%" "%LOCAL_PATH%"
py update_to_s3.py "%BUCKET2%" "%LOCAL_PATH%"
 
:: This will be ran on a loop until exit.
call loop_sync.bat