@echo off
rem RTK模拟器启动脚本
echo 启动RTK模拟器...

rem 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请安装Python 3.6或更高版本
    pause
    exit /b 1
)

rem 检查是否存在tkinter
python -c "import tkinter" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 警告: 未找到tkinter模块，将使用命令行版本
    goto :CLI_VERSION
)

rem 运行GUI版本
echo 启动GUI版本...
echo 使用端口60001和本机IP 192.168.2.12...
python "%~dp0\rtk_simulator.py" --remote-ip 192.168.2.12 --remote-port 60001 %*
goto :EOF

:CLI_VERSION
echo 启动命令行版本...
echo 使用端口60001和本机IP 192.168.2.12...
python "%~dp0\cli_rtk_simulator.py" --remote-ip 192.168.2.12 --remote-port 60001 %*

:EOF
echo 如果要退出，请按Ctrl+C
pause 