@echo off
echo =====================================================
echo               登高车 ESP32 控制板模拟器
echo =====================================================
echo 此模拟器会模拟登高车ESP32控制板，监听5300端口
echo 当收到命令时，会解析命令并显示对应的操作
echo 使用Ctrl+C可以退出模拟器
echo =====================================================
echo.

:: 检查Python是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请确保已安装Python并添加到PATH环境变量中
    pause
    exit /b 1
)

:: 检查依赖是否已安装
echo [信息] 检查必要的依赖...
python -c "import colorama" > nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 正在安装colorama模块...
    pip install colorama
    if %errorlevel% neq 0 (
        echo [错误] 安装colorama失败
        pause
        exit /b 1
    ) else (
        echo [成功] colorama安装成功
    )
) else (
    echo [信息] colorama已安装
)

echo.
echo [信息] 正在启动登高车模拟器...
echo [信息] 监听: 127.0.0.1:5300
echo.

:: 运行模拟器
python lift_car_simulator.py

:: 如果模拟器异常退出，暂停以便查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo [错误] 登高车模拟器异常退出，错误代码: %errorlevel%
    pause
) 