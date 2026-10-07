@echo off
setlocal
cd /d "%~dp0"
start "Local Notebook Server" cmd /k py "%~dp0server.py"
timeout /t 2 /nobreak >nul
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if exist "%CHROME%" (
  start "" "%CHROME%" http://127.0.0.1:8787
) else (
  start "" http://127.0.0.1:8787
)
endlocal
