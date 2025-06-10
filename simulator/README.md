# RTK 模拟器

这是一个用于模拟RTK（实时动态）设备数据的工具。该模拟器可以模拟多个RTK设备，通过UDP协议发送ENU（东-北-上）坐标数据。

## 功能特点

- 支持模拟多个RTK设备
- 提供图形界面和命令行两种使用方式
- 支持多种运动模式：静止、圆周运动、线性运动和随机游走
- 数据格式与ESP32 RTK设备兼容
- 可自定义参考坐标点、噪声级别和移动速度

## 安装依赖

模拟器使用Python编写，需要Python 3.6或更高版本。GUI版本需要安装tkinter库。

```bash
# Windows (命令提示符)
pip install -r requirements.txt

# Linux/macOS
pip3 install -r requirements.txt
```

## 快速开始

### 使用GUI版本

Windows:
```
run_rtk_simulator.bat
```

Linux/macOS:
```
./run_rtk_simulator.sh
```

或直接运行Python脚本:
```
python simulator/rtk_simulator.py
```

### 使用命令行版本

Windows:
```
python simulator/cli_rtk_simulator.py --remote-ip 192.168.3.8 --remote-port 60488 --num-devices 3
```

Linux/macOS:
```
python3 simulator/cli_rtk_simulator.py --remote-ip 192.168.3.8 --remote-port 60488 --num-devices 3
```

## 命令行参数

命令行版本支持以下参数:

```
--remote-ip    目标服务器IP地址 (默认: 127.0.0.1)
--remote-port  目标服务器端口 (默认: 60488)
--ref-lat      参考纬度 (默认: 32.0806422)
--ref-lon      参考经度 (默认: 119.301785)
--ref-alt      参考高度 (默认: 66.0)
--num-devices  模拟RTK设备数量 (默认: 1)
--movement     运动模式，可选: static, circular, linear, random (默认: circular)
--speed        运动速度 (m/s) (默认: 0.1)
--noise        噪声级别 (m) (默认: 0.01)
--local-ip     本地IP地址 (默认: 127.0.0.1)
```

例如，要启动3个使用圆周运动模式、速度为0.2m/s的RTK设备:

```
python simulator/cli_rtk_simulator.py --num-devices 3 --movement circular --speed 0.2
```

## 数据格式

模拟器发送的UDP数据包格式如下:

- 总长度: 16字节
- 前4字节: 时间戳(毫秒)，无符号32位整数，小端序
- 接下来4字节: E坐标(米)，32位浮点数，小端序
- 接下来4字节: N坐标(米)，32位浮点数，小端序
- 最后4字节: U坐标(米)，32位浮点数，小端序

这与ESP32 RTK设备发送的数据格式兼容。

## 图形界面使用说明

1. **全局设置**:
   - 设置目标服务器IP地址和端口
   - 设置参考点坐标（纬度、经度、高度）

2. **添加设备**:
   - 输入设备ID和IP地址
   - 选择运动模式，设置速度和噪声级别
   - 点击"添加设备"按钮

3. **设备控制**:
   - 可以单独启动/停止选中的设备
   - 也可以启动/停止所有设备
   - 可以删除选中的设备

## 开发者信息

### 主要文件

- `rtk_simulator.py`: GUI版本的主程序
- `cli_rtk_simulator.py`: 命令行版本的主程序
- `rtk_simulator_utils.py`: 共用的工具函数
- `run_rtk_simulator.bat`: Windows启动脚本
- `run_rtk_simulator.sh`: Linux/macOS启动脚本

### 扩展开发

如果需要修改或扩展模拟器功能，可以:

1. 添加新的运动模式: 在`RtkDevice`类的`_update_position`方法中添加
2. 更改数据格式: 修改`_send_udp_packet`方法
3. 添加更多模拟参数: 扩展`__init__`方法和命令行参数 