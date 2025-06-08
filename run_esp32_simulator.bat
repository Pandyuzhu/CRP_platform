@echo off
echo 正在启动ESP32模拟器...
echo 此模拟器会模拟两个ESP32控制板，分别监听5200和5201端口
echo.

cd simulator
call run_esp32_simulator.bat

:: 检查Python是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请确保已安装Python并添加到PATH环境变量中
    pause
    exit /b 1
)

:: 运行模拟器
python esp32_simulator.py

:: 如果模拟器异常退出，暂停以便查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo ESP32模拟器异常退出，错误代码: %errorlevel%
    pause
) 