import socket
import struct
import threading
import time
import math
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Tuple, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认参数
DEFAULT_REMOTE_IP = "192.168.1.100"  # 修改为ESP32的IP地址
DEFAULT_REMOTE_PORT = 60001  # 目标端口
DEFAULT_SEND_INTERVAL = 0.1  # 10Hz

class RTKDevice:
    """模拟RTK设备类"""
    
    def __init__(self, device_id: str, ip_address: str, radius: float = 0.01, 
                 speed: float = 0.1, base_coords: Tuple[float, float, float] = (0, 0, 0),
                 pattern: str = "circular", is_base_station: bool = False, device_number: str = None):
        self.device_id = device_id
        self.ip_address = ip_address
        self.radius = radius
        self.speed = speed
        self.base_coords = base_coords
        self.pattern = pattern
        self.is_base_station = is_base_station
        self.device_number = device_number if device_number else "1"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 使用UDP进行通信
        self.angle = 0.0
        self.running = False
        self.position = {"e": base_coords[0], "n": base_coords[1], "u": base_coords[2]}
        
    def start(self):
        """启动设备并发送数据"""
        self.running = True
        self._run()
        
    def _run(self):
        """设备运行线程"""
        while self.running:
            self._update_position()
            self._send_data()
            time.sleep(0.1)  # 模拟发送频率
            
    def _update_position(self):
        """根据运动模式更新位置"""
        if self.pattern == "circular":
            self._circular_motion()
        
    def _circular_motion(self):
        """圆周运动"""
        self.angle += (self.speed / self.radius) * 0.1  # 计算角度
        self.position = {
            "e": self.base_coords[0] + self.radius * math.cos(self.angle),
            "n": self.base_coords[1] + self.radius * math.sin(self.angle),
            "u": self.base_coords[2]
        }
        
    def _send_data(self):
        """通过UDP发送数据"""
        packet = self._create_packet()
        self.socket.sendto(packet, (self.ip_address, DEFAULT_REMOTE_PORT))  # 发送数据到ESP32的IP地址
        logger.info(f"已发送数据到 {self.device_id}")
        
    def _create_packet(self):
        """创建数据包，包含时间戳和位置"""
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        data = struct.pack('<Ifff', timestamp, self.position["e"], self.position["n"], self.position["u"])
        return data

class RTKSimulatorGUI:
    """RTK模拟器GUI类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RTK设备模拟器")
        self.root.geometry("800x600")
        self.devices: Dict[str, RTKDevice] = {}
        self._create_widgets()
        
    def _create_widgets(self):
        """创建GUI组件"""
        ttk.Button(self.root, text="启动设备", command=self._start_device).pack()
        ttk.Button(self.root, text="停止设备", command=self._stop_device).pack()

        self.device_id_var = tk.StringVar()
        self.device_ip_var = tk.StringVar()

        ttk.Label(self.root, text="设备ID:").pack()
        ttk.Entry(self.root, textvariable=self.device_id_var).pack()

        ttk.Label(self.root, text="设备IP:").pack()
        ttk.Entry(self.root, textvariable=self.device_ip_var).pack()

    def _start_device(self):
        """启动新设备"""
        device_id = self.device_id_var.get().strip()
        ip_address = self.device_ip_var.get().strip()
        if not device_id or not ip_address:
            messagebox.showerror("错误", "设备ID和IP地址不能为空")
            return
        
        device = RTKDevice(device_id=device_id, ip_address=ip_address)
        self.devices[device_id] = device
        device.start()

        logger.info(f"已启动设备: {device_id}")
    
    def _stop_device(self):
        """停止设备"""
        device_id = self.device_id_var.get().strip()
        if device_id not in self.devices:
            messagebox.showerror("错误", f"设备 {device_id} 不存在")
            return
        
        device = self.devices[device_id]
        device.running = False
        del self.devices[device_id]
        logger.info(f"已停止设备: {device_id}")

def main():
    """主函数"""
    root = tk.Tk()
    app = RTKSimulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
