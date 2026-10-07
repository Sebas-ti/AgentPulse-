@echo off
setlocal
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ezwinports.make_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\make.exe" (
    "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ezwinports.make_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\make.exe" %*
    exit /b %ERRORLEVEL%
)
for /f "delims=" %%I in ('where make.exe 2^>nul') do (
    if /i not "%%~nxI"=="make.bat" (
        "%%I" %*
        exit /b %ERRORLEVEL%
    )
)
echo [ERROR] make.exe is not installed or not found.
exit /b 1
