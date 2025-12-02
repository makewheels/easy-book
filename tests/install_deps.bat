@echo off
echo Installing Easy Book Automation Test Dependencies...

REM 检查虚拟环境是否存在
if not exist "..\.venv" (
    echo Creating virtual environment...
    python -m venv ..\.venv
)

echo.
echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat

echo.
echo Installing test dependencies...
pip install selenium pymongo requests webdriver-manager pytest

echo.
echo Dependencies installation complete!
echo.
echo You can now run the automation test with:
echo   cd tests
echo   ..\.venv\Scripts\python.exe automation.py
echo.
pause