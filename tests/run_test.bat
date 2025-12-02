@echo off
echo Running Easy Book Automation Test...

REM 激活虚拟环境
call ..\.venv\Scripts\activate.bat

REM 运行自动化测试
python automation.py

echo.
echo Test execution complete.
echo.
pause