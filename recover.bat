@echo off

:: This is run whenever corrupted files are detected, or manually.
echo This will now try to recover file(s).

py corrupt_fix.py "%LOCAL_PATH%"

if errorlevel 1 (
    echo Some files could not be repaired locally.
    echo Trying S3 version restore from %BUCKET%...
    py failed_recovery.py "%LOCAL_PATH%" "%BUCKET%" "backups"

    echo Trying S3 version restore from %BUCKET2%...
    py failed_recovery.py "%LOCAL_PATH%" "%BUCKET2%" "backups"
) else (
    echo All corrupted files were repaired or no corrupted files were found.
)