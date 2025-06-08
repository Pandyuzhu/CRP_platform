@echo off
echo =====================================================
echo              CRP平台 模拟器启动程序
echo =====================================================
echo 此脚本将启动以下模拟器:
echo 1. ESP32控制板模拟器 (搅拌机和喷射机)
echo 2. 登高车ESP32控制板模拟器
echo =====================================================
echo.

echo [信息] 正在启动ESP32控制板模拟器...
start cmd /k "cd simulator && run_esp32_simulator.bat"

echo [信息] 正在启动登高车ESP32控制板模拟器...
start cmd /k "cd simulator && run_lift_car_simulator.bat"

echo.
echo [成功] 所有模拟器已启动
echo 您可以在各自的窗口中查看模拟器状态
echo 关闭本窗口不会影响模拟器的运行
echo.
echo 按任意键退出...
pause > nul 