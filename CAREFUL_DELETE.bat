:: DELETE BUCKET BE CAREFUL WITH THIS
@echo off
set BUCKET=new-bucket-demo-test-1
set BUCKET2=new-bucket-demo-test-2

for /f "usebackq delims=" %%i in (`aws s3api list-object-versions --bucket %BUCKET% --output json`) do set JSON=%%i

powershell -NoProfile -Command ^
  "$b='%BUCKET%';" ^
  "$data = aws s3api list-object-versions --bucket $b | ConvertFrom-Json;" ^
  "if ($data.Versions) { foreach ($v in $data.Versions) { aws s3api delete-object --bucket $b --key $v.Key --version-id $v.VersionId } };" ^
  "if ($data.DeleteMarkers) { foreach ($m in $data.DeleteMarkers) { aws s3api delete-object --bucket $b --key $m.Key --version-id $m.VersionId } };" ^
  "aws s3api delete-bucket --bucket $b"


for /f "usebackq delims=" %%i in (`aws s3api list-object-versions --bucket %BUCKET2% --output json`) do set JSON=%%i

powershell -NoProfile -Command ^
  "$b='%BUCKET2%';" ^
  "$data = aws s3api list-object-versions --bucket $b | ConvertFrom-Json;" ^
  "if ($data.Versions) { foreach ($v in $data.Versions) { aws s3api delete-object --bucket $b --key $v.Key --version-id $v.VersionId } };" ^
  "if ($data.DeleteMarkers) { foreach ($m in $data.DeleteMarkers) { aws s3api delete-object --bucket $b --key $m.Key --version-id $m.VersionId } };" ^
  "aws s3api delete-bucket --bucket $b"
