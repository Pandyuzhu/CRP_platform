import socket

# 创建 UDP 套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定到本地所有网卡的指定端口（这里用 12345，可自定义）
local_port = 8888
sock.bind(('0.0.0.0', local_port))  # '0.0.0.0' 表示监听所有可用网卡

print(f"UDP 监听已启动，等待数据... 端口: {local_port}")

try:
    while True:
        # 接收数据（最多接收 1024 字节）
        data, addr = sock.recvfrom(1024)  # 阻塞直到有数据到达
        print(f"\n检测到来自 {addr} 的 UDP 数据！")
        print(f"数据内容: {data.decode('utf-8', errors='ignore')}")  # 尝试解码为字符串（忽略乱码）
except KeyboardInterrupt:
    print("\n程序已退出")
finally:
    sock.close()