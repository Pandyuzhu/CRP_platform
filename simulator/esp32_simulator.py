#!/usr/bin/env python
"""
ESP32模拟器 - 用于模拟ESP32控制板接收命令
此程序会创建两个TCP服务器，分别监听5200和5201端口，模拟两个ESP32控制板
当收到命令时，会解析16进制代码并显示对应的操作
"""

import socket
import threading
import time
import sys
import signal
import struct
import os
import datetime
from colorama import Fore, Back, Style, init

# 初始化colorama
init(autoreset=True)

# 控制板1的按钮定义 (搅拌机1和喷射机)
BOARD1_BUTTONS = {
    0x0001: {"name": "搅拌运行", "action": "启动", "component": "搅拌机1", "color": Fore.GREEN},
    0x0002: {"name": "搅拌停止", "action": "停止", "component": "搅拌机1", "color": Fore.RED},
    0x0004: {"name": "输送启动", "action": "启动", "component": "搅拌机1", "color": Fore.GREEN},
    0x0008: {"name": "输送停止", "action": "停止", "component": "搅拌机1", "color": Fore.RED},
    0x0010: {"name": "喷浆启动", "action": "启动", "component": "喷射机", "color": Fore.GREEN},
    0x0020: {"name": "喷浆停止", "action": "停止", "component": "喷射机", "color": Fore.RED},
    0x0040: {"name": "水泵启动", "action": "启动", "component": "搅拌机1", "color": Fore.GREEN},
    0x0080: {"name": "水泵停止", "action": "停止", "component": "搅拌机1", "color": Fore.RED},
    0x0100: {"name": "水阀启动", "action": "启动", "component": "搅拌机1", "color": Fore.GREEN},
    0x0200: {"name": "水阀停止", "action": "停止", "component": "搅拌机1", "color": Fore.RED}
}

# 控制板2的按钮定义 (搅拌机2和末端喷头)
BOARD2_BUTTONS = {
    0x0001: {"name": "搅拌运行", "action": "启动", "component": "搅拌机2", "color": Fore.GREEN},
    0x0002: {"name": "搅拌停止", "action": "停止", "component": "搅拌机2", "color": Fore.RED},
    0x0004: {"name": "输送启动", "action": "启动", "component": "搅拌机2", "color": Fore.GREEN},
    0x0008: {"name": "输送停止", "action": "停止", "component": "搅拌机2", "color": Fore.RED},
    0x0010: {"name": "水泵启动", "action": "启动", "component": "搅拌机2", "color": Fore.GREEN},
    0x0020: {"name": "水泵停止", "action": "停止", "component": "搅拌机2", "color": Fore.RED},
    0x0040: {"name": "水阀启动", "action": "启动", "component": "搅拌机2", "color": Fore.GREEN},
    0x0080: {"name": "水阀停止", "action": "停止", "component": "搅拌机2", "color": Fore.RED},
    0x0100: {"name": "纤维喷射启动", "action": "启动", "component": "末端喷头", "color": Fore.GREEN},
    0x0200: {"name": "纤维喷射停止", "action": "停止", "component": "末端喷头", "color": Fore.RED},
    0x0400: {"name": "浆料喷射启动", "action": "启动", "component": "末端喷头", "color": Fore.GREEN},
    0x0800: {"name": "浆料喷射停止", "action": "停止", "component": "末端喷头", "color": Fore.RED}
}

# 全局变量，用于控制线程退出
running = True

# 存储设备当前状态
board1_status = {}
board2_status = {}
# 状态锁
status_lock = threading.Lock()

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印表头"""
    clear_screen()
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")
    print(f"{Fore.CYAN}{Style.BRIGHT}              ESP32 控制板模拟器")
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")
    print(f"{Fore.YELLOW}控制板1 (IP: 192.168.3.120, 端口: 5200) - 搅拌机1和喷射机")
    print(f"{Fore.YELLOW}控制板2 (IP: 192.168.3.121, 端口: 5201) - 搅拌机2和末端喷头")
    print(f"{Fore.CYAN}{Style.BRIGHT}===========================================================")

def print_status():
    """打印当前设备状态"""
    with status_lock:
        # 搅拌机1状态
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} 搅拌机1状态 ")
        print(f"搅拌功能: {Fore.GREEN}运行中" if board1_status.get("搅拌", False) else f"搅拌功能: {Fore.RED}已停止")
        print(f"输送功能: {Fore.GREEN}运行中" if board1_status.get("输送", False) else f"输送功能: {Fore.RED}已停止")
        print(f"水泵功能: {Fore.GREEN}运行中" if board1_status.get("水泵", False) else f"水泵功能: {Fore.RED}已停止")
        print(f"水阀功能: {Fore.GREEN}运行中" if board1_status.get("水阀", False) else f"水阀功能: {Fore.RED}已停止")
        
        # 喷射机状态
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} 喷射机状态 ")
        print(f"喷浆功能: {Fore.GREEN}运行中" if board1_status.get("喷浆", False) else f"喷浆功能: {Fore.RED}已停止")
        
        # 搅拌机2状态
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} 搅拌机2状态 ")
        print(f"搅拌功能: {Fore.GREEN}运行中" if board2_status.get("搅拌", False) else f"搅拌功能: {Fore.RED}已停止")
        print(f"输送功能: {Fore.GREEN}运行中" if board2_status.get("输送", False) else f"输送功能: {Fore.RED}已停止")
        print(f"水泵功能: {Fore.GREEN}运行中" if board2_status.get("水泵", False) else f"水泵功能: {Fore.RED}已停止")
        print(f"水阀功能: {Fore.GREEN}运行中" if board2_status.get("水阀", False) else f"水阀功能: {Fore.RED}已停止")
        
        # 末端喷头状态
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} 末端喷头状态 ")
        print(f"纤维喷射: {Fore.GREEN}运行中" if board2_status.get("纤维喷射", False) else f"纤维喷射: {Fore.RED}已停止")
        print(f"浆料喷射: {Fore.GREEN}运行中" if board2_status.get("浆料喷射", False) else f"浆料喷射: {Fore.RED}已停止")

def print_command_log(board_id, cmd_value, button_info, log_list):
    """添加命令日志"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    component = button_info.get("component", "未知")
    name = button_info.get("name", "未知命令")
    action = button_info.get("action", "未知")
    color = button_info.get("color", Fore.WHITE)
    
    log_entry = f"{timestamp} | 控制板{board_id} | {component} | {color}{name} ({action}){Style.RESET_ALL} | 0x{cmd_value:04X}"
    log_list.append(log_entry)
    
    # 只保留最近的10条记录
    if len(log_list) > 10:
        log_list.pop(0)

def update_device_status(board_id, button_info):
    """更新设备状态"""
    with status_lock:
        if board_id == 1:
            status_dict = board1_status
        else:
            status_dict = board2_status
        
        name = button_info.get("name", "")
        action = button_info.get("action", "")
        
        # 根据按钮名称和动作更新状态
        if "搅拌" in name:
            status_dict["搅拌"] = (action == "启动")
        elif "输送" in name:
            status_dict["输送"] = (action == "启动")
        elif "水泵" in name:
            status_dict["水泵"] = (action == "启动")
        elif "水阀" in name:
            status_dict["水阀"] = (action == "启动")
        elif "喷浆" in name:
            status_dict["喷浆"] = (action == "启动")
        elif "纤维喷射" in name:
            status_dict["纤维喷射"] = (action == "启动")
        elif "浆料喷射" in name:
            status_dict["浆料喷射"] = (action == "启动")

# 命令日志
command_logs = []

def handle_client(client_socket, board_id, buttons_map):
    """处理客户端连接"""
    try:
        client_addr = client_socket.getpeername()
        print(f"{Fore.CYAN}[ESP32模拟器] 控制板{board_id}收到新连接: {client_addr}")
        
        # 接收命令
        data = client_socket.recv(1024)
        
        if data:
            print(f"{Fore.CYAN}[ESP32模拟器] 收到原始数据: {data.hex()}")
            
            # 解析16进制命令
            if len(data) >= 2:
                # 从网络字节序（大端序）解析命令
                cmd_value = struct.unpack('>H', data[:2])[0]
                
                # 查找命令对应的按钮
                button_info = buttons_map.get(cmd_value, None)
                
                if button_info:
                    # 更新设备状态
                    update_device_status(board_id, button_info)
                    
                    # 记录命令日志
                    print_command_log(board_id, cmd_value, button_info, command_logs)
                    
                    # 刷新显示
                    print_header()
                    print_status()
                    
                    # 打印命令日志
                    print(f"\n{Back.WHITE}{Fore.BLACK}{Style.BRIGHT} 命令日志 (最近10条) ")
                    for log in command_logs:
                        print(log)
                else:
                    print(f"\n{Fore.RED}接收到未知命令: 控制板{board_id} - 0x{cmd_value:04X}")
            else:
                print(f"{Fore.RED}接收到无效数据: 控制板{board_id} - {data.hex()}")
        
            # 发送响应确认
            client_socket.send(b'\x01')
            print(f"{Fore.GREEN}[ESP32模拟器] 已发送确认响应")
    except Exception as e:
        print(f"{Fore.RED}处理客户端时出错: {e}")
    finally:
        client_socket.close()
        print(f"{Fore.YELLOW}[ESP32模拟器] 连接已关闭: 控制板{board_id}")

def start_server(host, port, board_id, buttons_map):
    """启动TCP服务器"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        server.settimeout(1.0)  # 设置超时，以便可以定期检查running标志
        
        while running:
            try:
                client, addr = server.accept()
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client, board_id, buttons_map)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                # 超时，继续循环
                continue
            except Exception as e:
                if running:
                    print(f"{Fore.RED}接受连接时出错: {e}")
                    time.sleep(1)
    except Exception as e:
        print(f"{Fore.RED}服务器启动失败: {e}")
    finally:
        server.close()

def signal_handler(sig, frame):
    """处理退出信号"""
    global running
    print(f"\n{Fore.YELLOW}正在退出...")
    running = False

def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 设置ESP32模拟板的IP和端口
    host = '0.0.0.0'  # 监听所有网络接口
    board1_port = 5200
    board2_port = 5201
    
    # 创建两个服务器线程
    board1_thread = threading.Thread(
        target=start_server,
        args=(host, board1_port, 1, BOARD1_BUTTONS)
    )
    board1_thread.daemon = True
    
    board2_thread = threading.Thread(
        target=start_server,
        args=(host, board2_port, 2, BOARD2_BUTTONS)
    )
    board2_thread.daemon = True
    
    # 打印初始状态
    print_header()
    print_status()
    
    print(f"\n{Back.WHITE}{Fore.BLACK}{Style.BRIGHT} 命令日志 (最近10条) ")
    print(f"{Fore.YELLOW}等待命令...")
    
    # 启动服务器线程
    board1_thread.start()
    board2_thread.start()
    
    # 主线程等待
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    
    # 等待服务器线程结束
    board1_thread.join(timeout=2.0)
    board2_thread.join(timeout=2.0)
    
    print(f"{Fore.YELLOW}已退出")

if __name__ == "__main__":
    main() 