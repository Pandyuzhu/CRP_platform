import socket
import numpy as np
import cv2
import time
import asyncio
import threading
import psutil
import os
import atexit
import signal
from fastapi import WebSocket
import logging

# 全局变量用于存储最新的图像数据
rgb_frame = None
depth_frame = None
rgb_frame_lock = threading.Lock()
depth_frame_lock = threading.Lock()

# 添加全局变量记录ZED相机连接状态
zed_connected = False
zed_connected_lock = threading.Lock()

# 用于优雅关闭的事件标志
shutdown_event = threading.Event()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zed_server")

def is_zed_connected():
    """
    返回ZED相机的连接状态
    """
    with zed_connected_lock:
        return zed_connected

def log_memory_usage():
    """
    记录当前进程的内存使用情况，不使用定时器，避免在关闭时出现问题
    """
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger.info(f"内存使用: {mem_info.rss / 1024 / 1024:.2f} MB (RSS), {mem_info.vms / 1024 / 1024:.2f} MB (VMS)")
    except Exception as e:
        # 捕获任何异常，防止在关闭过程中崩溃
        pass

def cleanup_resources():
    """
    清理资源的函数，在程序退出时调用
    """
    logger.info("正在清理ZED服务器资源...")
    # 设置关闭事件，通知所有线程退出
    shutdown_event.set()
    # 给线程一些时间来退出
    time.sleep(0.5)
    logger.info("ZED服务器资源清理完成")

def start_zed_server(host='0.0.0.0', port=5060):
    """
    启动ZED相机数据接收服务器（在单独线程中运行）
    """
    global rgb_frame, depth_frame, zed_connected

    # 初始化 socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    # 设置socket超时，这样可以定期检查shutdown_event
    server_socket.settimeout(1.0)

    logger.info(f"🖥️ ZED服务器等待客户端连接: {host}:{port} ...")
    
    # 注册退出处理函数
    atexit.register(cleanup_resources)
    
    try:
        # 记录初始内存使用情况
        log_memory_usage()
        
        last_mem_log_time = time.time()
        
        while not shutdown_event.is_set():
            try:
                # 等待连接，带有超时，可以检查shutdown_event
                conn, addr = server_socket.accept()
                logger.info(f"✅ 已连接ZED客户端：{addr}")
                
                # 更新ZED相机连接状态为已连接
                with zed_connected_lock:
                    zed_connected = True
                    
                conn.settimeout(2.0)
                
                try:
                    while not shutdown_event.is_set():
                        try:
                            # 1. 接收深度图
                            size_data = conn.recv(4)
                            if not size_data:
                                break
                            img_size = int.from_bytes(size_data, byteorder='big')
                            data = b''
                            while len(data) < img_size:
                                packet = conn.recv(img_size - len(data))
                                if not packet:
                                    break
                                data += packet

                            np_arr = np.frombuffer(data, np.uint8)
                            depth_img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
                            
                            if depth_img is not None:
                                # 生成深度热力图
                                DEPTH_NEAR = 800    # 最近的喷涂厚度边界
                                DEPTH_FAR = 1200    # 最远的允许喷涂边界

                                depth_float = depth_img.astype(np.float32)
                                depth_float = np.nan_to_num(depth_float, nan=0.0)
                                depth_clip = np.clip(depth_float, DEPTH_NEAR, DEPTH_FAR)
                                depth_norm = (depth_clip - DEPTH_NEAR) / (DEPTH_FAR - DEPTH_NEAR)
                                depth_vis = (depth_norm * 255).astype(np.uint8)
                                depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
                                
                                # 更新全局深度图帧
                                with depth_frame_lock:
                                    depth_frame = depth_vis

                            # 2. 接收 RGB 图
                            size_data = conn.recv(4)
                            if not size_data:
                                break
                            img_size = int.from_bytes(size_data, byteorder='big')
                            data = b''
                            while len(data) < img_size:
                                packet = conn.recv(img_size - len(data))
                                if not packet:
                                    break
                                data += packet

                            np_arr = np.frombuffer(data, np.uint8)
                            rgb_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                            
                            if rgb_img is not None:
                                # 更新全局RGB帧
                                with rgb_frame_lock:
                                    rgb_frame = rgb_img
                            
                            # 定期记录内存使用情况，但不使用定时器
                            current_time = time.time()
                            if current_time - last_mem_log_time > 60:  # 每60秒记录一次
                                log_memory_usage()
                                last_mem_log_time = current_time
                            
                        except socket.timeout:
                            logger.warning("⏳ 接收超时，等待下一帧")
                            continue
                        except Exception as e:
                            if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
                                logger.error(f"❌ 处理帧时出现错误：{e}")
                            break
                finally:
                    conn.close()
                    # 更新ZED相机连接状态为已断开
                    with zed_connected_lock:
                        zed_connected = False
                    if not shutdown_event.is_set():  # 只在非关闭状态下记录日志
                        logger.info("ZED客户端连接已关闭，等待新连接...")
            except socket.timeout:
                # 接收超时，继续检查shutdown_event
                continue
            except Exception as e:
                if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
                    logger.error(f"ZED服务器异常：{e}")
    finally:
        server_socket.close()
        # 确保在服务器关闭时，ZED相机状态为断开
        with zed_connected_lock:
            zed_connected = False
        # 取消注册退出处理函数，避免重复调用
        atexit.unregister(cleanup_resources)
        if not shutdown_event.is_set():  # 只在非关闭状态下记录日志
            logger.info("ZED服务器已关闭")

# 信号处理函数
def signal_handler(sig, frame):
    logger.info(f"收到信号 {sig}，正在优雅关闭...")
    shutdown_event.set()

# 启动ZED服务器线程
def init_zed_server():
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动线程
    zed_thread = threading.Thread(target=start_zed_server, daemon=True)
    zed_thread.start()
    return zed_thread 