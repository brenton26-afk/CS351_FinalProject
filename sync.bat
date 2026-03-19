@echo off

py sync_to_s3.py "%BUCKET%" "%LOCAL_PATH%" "backups"
if errorlevel 1 (
    echo sync_to_s3.py failed for %BUCKET%
    exit /b 1
)

py sync_to_s3.py "%BUCKET2%" "%LOCAL_PATH%" "backups"
if errorlevel 1 (
    echo sync_to_s3.py failed for %BUCKET2%
    exit /b 1
)

py corruption_scanner.py "%LOCAL_PATH%"
if errorlevel 1 (
    echo Corrupted files were found.
    call recover.bat
) else (
    echo No corrupted files found.
)