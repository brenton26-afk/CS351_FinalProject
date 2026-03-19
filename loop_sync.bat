@echo off

::sync buckets constantly
set INTERVAL=10
:loop
call sync.bat
timeout /t %INTERVAL% >nul
goto loop