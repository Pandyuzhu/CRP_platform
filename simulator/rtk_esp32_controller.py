import socket
import json
import tkinter as tk
from tkinter import ttk, messagebox

# ESP32 的局域网 IP 和监听端口
ESP32_IP = "192.168.3.62"  # 请根据你的实际 ESP32 IP 修改
ESP32_PORT = 12345         # 必须与 ESP32 接收端代码中保持一致

class UDPClient:
    def __init__(self, target_ip, target_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (target_ip, target_port)

    def send_message(self, message: str):
        self.sock.sendto(message.encode(), self.target)

    def close(self):
        self.sock.close()

class RtkSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RTK设备模拟器控制器")
        self.root.geometry("600x200")
        self.client = UDPClient(ESP32_IP, ESP32_PORT)
        self._create_widgets()

    def _create_widgets(self):
        control_frame = ttk.LabelFrame(self.root, text="全局设置", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="目标服务器IP:").grid(row=0, column=0)
        self.remote_ip_var = tk.StringVar(value="10.192.32.169")
        ttk.Entry(control_frame, textvariable=self.remote_ip_var, width=18).grid(row=0, column=1)

        ttk.Label(control_frame, text="目标端口:").grid(row=0, column=2)
        self.remote_port_var = tk.StringVar(value="60001")
        ttk.Entry(control_frame, textvariable=self.remote_port_var, width=8).grid(row=0, column=3)

        ttk.Label(control_frame, text="参考纬度:").grid(row=1, column=0)
        self.ref_lat_var = tk.StringVar(value="32.0806422")
        ttk.Entry(control_frame, textvariable=self.ref_lat_var, width=18).grid(row=1, column=1)

        ttk.Label(control_frame, text="参考经度:").grid(row=1, column=2)
        self.ref_lon_var = tk.StringVar(value="119.301785")
        ttk.Entry(control_frame, textvariable=self.ref_lon_var, width=18).grid(row=1, column=3)

        ttk.Label(control_frame, text="参考高度(m):").grid(row=1, column=4)
        self.ref_alt_var = tk.StringVar(value="66.0")
        ttk.Entry(control_frame, textvariable=self.ref_alt_var, width=10).grid(row=1, column=5)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="启动模拟", command=self.start_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止模拟", command=self.stop_simulation).pack(side=tk.LEFT, padx=5)

    def start_simulation(self):
        params = {
            "command": "start",
            "target_ip": self.remote_ip_var.get(),
            "target_port": int(self.remote_port_var.get()),
            "ref_lat": float(self.ref_lat_var.get()),
            "ref_lon": float(self.ref_lon_var.get()),
            "ref_alt": float(self.ref_alt_var.get())
        }
        message = json.dumps(params)
        self.client.send_message(message)
        messagebox.showinfo("启动成功", "已发送启动命令和参数到ESP32")

    def stop_simulation(self):
        self.client.send_message(json.dumps({"command": "stop"}))
        messagebox.showinfo("停止成功", "已发送停止命令到ESP32")

    def close(self):
        self.client.close()
        self.root.quit()

def main():
    root = tk.Tk()
    app = RtkSimulatorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

if __name__ == "__main__":
    main()
