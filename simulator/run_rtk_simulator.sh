#!/bin/bash
# RTK模拟器启动脚本
echo "启动RTK模拟器..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请安装Python 3.6或更高版本"
    exit 1
fi

# 检查是否存在tkinter
if python3 -c "import tkinter" &> /dev/null; then
    # 运行GUI版本
    echo "启动GUI版本..."
    python3 "$(dirname "$0")/rtk_simulator.py" "$@"
else
    # 运行命令行版本
    echo "警告: 未找到tkinter模块，将使用命令行版本"
    echo "启动命令行版本..."
    python3 "$(dirname "$0")/cli_rtk_simulator.py" "$@"
fi

echo "如果要退出，请按Ctrl+C" 