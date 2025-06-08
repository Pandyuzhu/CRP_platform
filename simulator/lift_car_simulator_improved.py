#!/usr/bin/env python
"""
改进版登高车模拟器 - 用于模拟登高车ESP32控制板接收命令
此程序会创建一个UDP服务器，监听5300端口，模拟登高车ESP32控制板
当收到命令时，会解析命令并显示对应的操作
"""

import socket
import threading
import time
import sys
import signal
import os
import datetime
from colorama import Fore, Back, Style, init

# 初始化colorama
init(autoreset=True)

# 登高车状态
lift_car_state = {
    "joint1": 0,  # 0=停止，1=伸展，2=屈曲
    "joint2": 0,  # 0=停止，1=伸展，2=屈曲
    "joint3": 0   # 0=停止，1=伸展，2=屈曲
}

# 状态锁
state_lock = threading.Lock()

# 全局变量，用于控制线程退出
running = True

# 命令日志
command_logs = []

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印表头"""
    clear_screen()
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")
    print(f"{Fore.CYAN}{Style.BRIGHT}               改进版登高车 ESP32 控制板模拟器")
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")
    print(f"{Fore.YELLOW}登高车 (IP: 127.0.0.1, 端口: 5300)")
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")

def print_status():
    """打印当前设备状态"""
    with state_lock:
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} 登高车状态 ")
        
        # 关节1状态
        joint1_state = lift_car_state["joint1"]
        if joint1_state == 1:
            print(f"关节1: {Fore.GREEN}伸展中")
        elif joint1_state == 2:
            print(f"关节1: {Fore.YELLOW}屈曲中")
        else:
            print(f"关节1: {Fore.RED}已停止")
        
        # 关节2状态
        joint2_state = lift_car_state["joint2"]
        if joint2_state == 1:
            print(f"关节2: {Fore.GREEN}伸展中")
        elif joint2_state == 2:
            print(f"关节2: {Fore.YELLOW}屈曲中")
        else:
            print(f"关节2: {Fore.RED}已停止")
        
        # 关节3状态
        joint3_state = lift_car_state["joint3"]
        if joint3_state == 1:
            print(f"关节3: {Fore.GREEN}伸展中")
        elif joint3_state == 2:
            print(f"关节3: {Fore.YELLOW}屈曲中")
        else:
            print(f"关节3: {Fore.RED}已停止")

def update_state(cmd_bytes):
    """更新设备状态"""
    global lift_car_state
    with state_lock:
        # 检查使能字节
        if cmd_bytes[0] != 1:
            # 如果不是1，则停止所有关节
            lift_car_state["joint1"] = 0
            lift_car_state["joint2"] = 0
            lift_car_state["joint3"] = 0
            return
        
        # 更新各关节状态
        lift_car_state["joint1"] = cmd_bytes[1]
        lift_car_state["joint2"] = cmd_bytes[2]
        lift_car_state["joint3"] = cmd_bytes[3]
        
        print(f"{Fore.GREEN}状态已更新: 关节1={lift_car_state['joint1']}, 关节2={lift_car_state['joint2']}, 关节3={lift_car_state['joint3']}")

def add_command_log(cmd_bytes, addr):
    """添加命令日志"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # 解析命令
    enable = cmd_bytes[0]
    joint1 = cmd_bytes[1]
    joint2 = cmd_bytes[2]
    joint3 = cmd_bytes[3]
    
    # 构建日志条目
    log_entry = f"{timestamp} | 来源: {addr[0]}:{addr[1]} | 使能: {enable} | 关节1: {joint1} | 关节2: {joint2} | 关节3: {joint3}"
    command_logs.append(log_entry)
    
    # 只保留最近的10条记录
    if len(command_logs) > 10:
        command_logs.pop(0)

def udp_server():
    """启动UDP服务器"""
    host = '0.0.0.0'  # 监听所有网络接口
    port = 5300
    
    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    sock.settimeout(1.0)  # 设置超时，以便可以定期检查running标志
    
    print(f"{Fore.GREEN}[登高车模拟器] 启动，监听 {host}:{port}")
    
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"\n{Fore.CYAN}[登高车模拟器] 收到来自 {addr} 的数据: {data.hex()}")
            
            if len(data) >= 4:
                # 打印详细的命令内容
                print(f"{Fore.YELLOW}命令内容: [使能={data[0]}, 关节1={data[1]}, 关节2={data[2]}, 关节3={data[3]}]")
                
                # 更新设备状态
                update_state(data)
                
                # 添加日志
                add_command_log(data, addr)
                
                # 刷新显示
                print_header()
                print_status()
                
                # 显示命令日志
                print(f"\n{Back.WHITE}{Fore.BLACK}{Style.BRIGHT} 命令日志 (最近10条) ")
                for log in command_logs:
                    print(log)
                
                # 发送响应确认
                try:
                    sock.sendto(b'\x01', addr)
                    print(f"{Fore.GREEN}[登高车模拟器] 已发送确认响应到 {addr}")
                except Exception as send_err:
                    print(f"{Fore.RED}[登高车模拟器] 发送确认时出错: {send_err}")
            else:
                print(f"{Fore.RED}[登高车模拟器] 接收到无效数据，长度不足4字节")
        except socket.timeout:
            # 超时继续循环
            continue
        except Exception as e:
            if running:
                print(f"{Fore.RED}[登高车模拟器] 接收数据时出错: {e}")
    
    sock.close()
    print(f"{Fore.YELLOW}[登高车模拟器] UDP服务器已关闭")

def signal_handler(sig, frame):
    """处理退出信号"""
    global running
    print(f"\n{Fore.YELLOW}[登高车模拟器] 正在退出...")
    running = False

def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 打印初始状态
    print_header()
    print_status()
    
    print(f"\n{Back.WHITE}{Fore.BLACK}{Style.BRIGHT} 命令日志 (最近10条) ")
    print(f"{Fore.YELLOW}等待命令...")
    
    # 启动UDP服务器
    udp_server()

if __name__ == "__main__":
    main() 