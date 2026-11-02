@echo off
if "%~1"=="" (
    echo Usage: %~nx0 "path\to\book"
    exit /b 1
)

set "BOOK_PATH=%~f1"
pushd "%~dp0"
if /I "%~2"=="--setup" (
    py book-comp.py "%BOOK_PATH%" --setup
) else (
    py book-comp.py "%BOOK_PATH%"
)
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%