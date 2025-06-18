import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# 配置UDP通信
ESP32_IP = "192.168.32.169"  # ESP32的IP地址
ESP32_PORT = 60001           # 目标端口

# 发送命令的UDP客户端
class UDPClient:
    def __init__(self, target_ip, target_port):
        self.target_ip = target_ip
        self.target_port = target_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def send_message(self, message: str):
        """向ESP32发送命令"""
        try:
            self.socket.sendto(message.encode('utf-8'), (self.target_ip, self.target_port))
            print(f"发送命令: {message}")
        except Exception as e:
            print(f"发送命令失败: {e}")

    def close(self):
        """关闭UDP连接"""
        self.socket.close()

# 创建GUI界面
class RtkSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RTK设备模拟器")
        self.root.geometry("800x600")
        self.client = UDPClient(ESP32_IP, ESP32_PORT)
        
        # 创建设备列表
        self.devices = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        # 控制区域
        control_frame = ttk.LabelFrame(self.root, text="控制区", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 启动按钮
        self.start_button = ttk.Button(control_frame, text="启动模拟", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # 停止按钮
        self.stop_button = ttk.Button(control_frame, text="停止模拟", command=self.stop_simulation)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 添加设备按钮
        self.add_device_button = ttk.Button(control_frame, text="添加设备", command=self.add_device)
        self.add_device_button.pack(side=tk.LEFT, padx=5)

        # 设备列表区域
        devices_frame = ttk.LabelFrame(self.root, text="设备列表", padding="10")
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview用于显示设备列表
        columns = ("device_id", "ip", "status")
        self.devices_tree = ttk.Treeview(devices_frame, columns=columns, show="headings")
        self.devices_tree.heading("device_id", text="设备ID")
        self.devices_tree.heading("ip", text="IP地址")
        self.devices_tree.heading("status", text="状态")

        self.devices_tree.pack(fill=tk.BOTH, expand=True)
    
    def add_device(self):
        """添加一个设备"""
        device_id = f"rtk{len(self.devices)+1}"
        ip = f"192.168.3.{len(self.devices)+1}"
        self.devices.append((device_id, ip, "未启动"))
        self._update_devices_tree()
    
    def _update_devices_tree(self):
        """更新设备列表界面"""
        for item in self.devices_tree.get_children():
            self.devices_tree.delete(item)

        for device in self.devices:
            self.devices_tree.insert("", "end", values=device)
    
    def start_simulation(self):
        """开始模拟"""
        self.client.send_message("start")
        messagebox.showinfo("模拟", "已启动模拟")
    
    def stop_simulation(self):
        """停止模拟"""
        self.client.send_message("stop")
        messagebox.showinfo("模拟", "已停止模拟")
    
    def close(self):
        """关闭UDP客户端"""
        self.client.close()
        self.root.quit()

# 创建并启动GUI
def main():
    root = tk.Tk()
    app = RtkSimulatorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)  # 确保关闭时释放资源
    root.mainloop()

if __name__ == "__main__":
    main()
