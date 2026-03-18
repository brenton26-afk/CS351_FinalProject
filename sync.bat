@echo off

::sync and detect corruption
py sync_to_s3.py "%BUCKET%" "%LOCAL_PATH%"
py sync_to_s3.py "%BUCKET2%" "%LOCAL_PATH%"
py corruption_scanner.py "%LOCAL_PATH%"

if %ERRORLEVEL% EQU 1 (
    echo Corrupted files were found.
    call recover.bat
) else (
    echo No corrupted files found.
)