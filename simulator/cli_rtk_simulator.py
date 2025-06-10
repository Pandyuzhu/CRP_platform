#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTK设备模拟器的命令行版本
"""

import argparse
import time
import socket
import struct
import math
import random
import threading
import sys
import signal
import json
import logging
from typing import List, Dict, Tuple
from rtk_simulator import RTKSimulator, RTKDevice

# WGS-84常量
WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)
DEG_TO_RAD = math.pi / 180.0

# 默认参数
DEFAULT_REF_LAT = 32.0806422
DEFAULT_REF_LON = 119.301785
DEFAULT_REF_ALT = 66.0
DEFAULT_REMOTE_IP = "192.168.2.12"  # 修改为本机IP
DEFAULT_REMOTE_PORT = 60001  # 修改为与后端一致的端口
DEFAULT_SEND_INTERVAL = 0.1  # 10Hz

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RtkDevice:
    """单个RTK设备模拟类"""
    
    def __init__(self, device_id: str, local_ip: str, 
                 remote_ip: str, remote_port: int, 
                 ref_lat: float, ref_lon: float, ref_alt: float,
                 movement_pattern: str = "circular",
                 movement_speed: float = 0.05,
                 noise_level: float = 0.01):
        """
        初始化RTK设备
        
        Args:
            device_id: 设备ID
            local_ip: 本地IP地址
            remote_ip: 目标服务器IP
            remote_port: 目标服务器端口
            ref_lat: 参考纬度(度)
            ref_lon: 参考经度(度)
            ref_alt: 参考高度(米)
            movement_pattern: 运动模式 ("static", "circular", "linear", "random")
            movement_speed: 运动速度(米/秒)
            noise_level: 噪声级别(米)
        """
        self.device_id = device_id
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        
        # 参考点
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.ref_alt = ref_alt
        
        # 计算参考点的ECEF坐标
        self.ref_ecef = self._geodetic_to_ecef(ref_lat, ref_lon, ref_alt)
        
        # 运动参数
        self.movement_pattern = movement_pattern
        self.movement_speed = movement_speed
        self.noise_level = noise_level
        
        # 当前ENU位置
        self.current_enu = [0.0, 0.0, 0.0]
        
        # 用于圆周运动和线性运动的参数
        self.movement_radius = 2.0  # 圆周运动半径(米)
        self.movement_angle = 0.0   # 当前角度(弧度)
        self.linear_direction = [1.0, 0.0, 0.0]  # 线性运动方向
        self.boundary = 10.0  # 线性运动的边界(米)
        
        # UDP套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 控制标志
        self.running = False
        self.thread = None
        
        # 时间戳和统计
        self.start_time_ms = 0
        self.packets_sent = 0
        
    def start(self):
        """启动RTK设备模拟"""
        if self.running:
            return
        
        self.running = True
        self.start_time_ms = int(time.time() * 1000)
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print(f"RTK设备 {self.device_id} ({self.local_ip}) 已启动")
    
    def stop(self):
        """停止RTK设备模拟"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        print(f"RTK设备 {self.device_id} ({self.local_ip}) 已停止")
    
    def _run(self):
        """运行模拟线程"""
        last_send_time = 0
        
        while self.running:
            current_time = time.time()
            elapsed_time = current_time - last_send_time
            
            # 按照指定间隔发送数据
            if elapsed_time >= DEFAULT_SEND_INTERVAL:
                # 更新位置
                self._update_position(elapsed_time)
                
                # 发送UDP数据包
                self._send_udp_packet()
                
                last_send_time = current_time
            
            # 避免CPU占用过高
            time.sleep(0.001)
    
    def _update_position(self, elapsed_time: float):
        """根据运动模式更新位置"""
        # 计算本次位移
        distance = self.movement_speed * elapsed_time
        
        if self.movement_pattern == "static":
            # 静止模式，仅添加随机噪声
            pass
        
        elif self.movement_pattern == "circular":
            # 圆周运动
            self.movement_angle += distance / self.movement_radius
            self.current_enu[0] = self.movement_radius * math.cos(self.movement_angle)
            self.current_enu[1] = self.movement_radius * math.sin(self.movement_angle)
        
        elif self.movement_pattern == "linear":
            # 线性往返运动
            for i in range(3):
                self.current_enu[i] += distance * self.linear_direction[i]
                
                # 检查是否达到边界，如果是则反向
                if abs(self.current_enu[i]) > self.boundary:
                    self.current_enu[i] = math.copysign(self.boundary, self.current_enu[i])
                    self.linear_direction[i] *= -1
        
        elif self.movement_pattern == "random":
            # 随机游走
            for i in range(3):
                step = distance * random.uniform(-1, 1)
                self.current_enu[i] += step
                
                # 保持在边界内
                self.current_enu[i] = max(-self.boundary, min(self.boundary, self.current_enu[i]))
        
        # 添加随机噪声
        for i in range(3):
            self.current_enu[i] += random.uniform(-self.noise_level, self.noise_level)
    
    def _send_udp_packet(self):
        """发送UDP数据包，格式与ESP32相同"""
        try:
            # 计算当前时间戳（毫秒）
            current_time_ms = int(time.time() * 1000) - self.start_time_ms
            
            # 创建UDP数据包，前8字节为设备ID，后16字节为数据
            packet = bytearray(24)  # 8字节设备ID + 16字节数据
            
            # 写入设备ID（最多8字节）
            device_id_bytes = self.device_id.encode('utf-8')
            for i in range(min(len(device_id_bytes), 8)):
                packet[i] = device_id_bytes[i]
            
            # 写入时间戳（4字节，uint32）
            struct.pack_into('<I', packet, 8, current_time_ms)
            
            # 写入ENU坐标（每个4字节，float）
            struct.pack_into('<f', packet, 12, self.current_enu[0])
            struct.pack_into('<f', packet, 16, self.current_enu[1])
            struct.pack_into('<f', packet, 20, self.current_enu[2])
            
            # 发送UDP数据包
            self.sock.sendto(packet, (self.remote_ip, self.remote_port))
            self.packets_sent += 1
            
            # 每100个包打印一次状态
            if self.packets_sent % 100 == 0:
                print(f"设备 {self.device_id}: 已发送 {self.packets_sent} 个数据包，当前ENU: "
                      f"E={self.current_enu[0]:.3f}, N={self.current_enu[1]:.3f}, U={self.current_enu[2]:.3f}")
                
        except Exception as e:
            print(f"发送UDP数据包时出错: {e}")
    
    def _geodetic_to_ecef(self, lat_deg: float, lon_deg: float, h: float) -> Tuple[float, float, float]:
        """将大地坐标转换为ECEF坐标"""
        lat = lat_deg * DEG_TO_RAD
        lon = lon_deg * DEG_TO_RAD
        a = WGS84_A
        e2 = WGS84_E2
        
        N = a / math.sqrt(1 - e2 * math.sin(lat) * math.sin(lat))
        x = (N + h) * math.cos(lat) * math.cos(lon)
        y = (N + h) * math.cos(lat) * math.sin(lon)
        z = (N * (1 - e2) + h) * math.sin(lat)
        
        return (x, y, z)
    
    def _ecef_to_enu(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """将ECEF坐标转换为ENU坐标"""
        x0, y0, z0 = self.ref_ecef
        lat0 = self.ref_lat * DEG_TO_RAD
        lon0 = self.ref_lon * DEG_TO_RAD
        
        dx = x - x0
        dy = y - y0
        dz = z - z0
        
        sin_lat = math.sin(lat0)
        cos_lat = math.cos(lat0)
        sin_lon = math.sin(lon0)
        cos_lon = math.cos(lon0)
        
        e = -sin_lon * dx + cos_lon * dy
        n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
        
        return (e, n, u)

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='RTK设备模拟器命令行工具')
    parser.add_argument('--target', type=str, default='127.0.0.1', help='目标服务器IP地址')
    parser.add_argument('--port', type=int, default=60001, help='目标服务器端口')
    parser.add_argument('--devices', type=int, default=2, help='模拟RTK设备数量')
    parser.add_argument('--basestation', action='store_true', help='是否包含基站')
    parser.add_argument('--ip-prefix', type=str, default='192.168.3.', help='IP地址前缀')
    parser.add_argument('--radius', type=float, default=0.01, help='运动半径（米）')
    parser.add_argument('--speed', type=float, default=0.1, help='运动速度（米/秒）')
    parser.add_argument('--center', type=str, default='0,0,0', help='中心坐标(E,N,U)')
    
    args = parser.parse_args()
    
    # 解析中心坐标
    try:
        center_coords = tuple(map(float, args.center.split(',')))
        if len(center_coords) != 3:
            raise ValueError("中心坐标需要3个值(E,N,U)")
    except Exception as e:
        logger.error(f"解析中心坐标时出错: {e}")
        center_coords = (0.0, 0.0, 0.0)
    
    # 创建模拟器
    simulator = RTKSimulator()
    simulator.set_target(args.target, args.port)
    
    # 创建RTK设备
    for i in range(args.devices):
        device_id = f"rtk{i+1}"
        ip_address = f"{args.ip_prefix}{61+i}"  # 从61开始
        
        # 为每个设备设置不同的坐标偏移
        offset = (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0)
        base_coords = (
            center_coords[0] + offset[0], 
            center_coords[1] + offset[1], 
            center_coords[2] + offset[2]
        )
        
        # 添加设备
        is_base = (i == 0 and args.basestation)
        simulator.add_device(
            device_id=device_id,
            ip_address=ip_address,
            radius=args.radius,
            speed=args.speed,
            base_coords=base_coords,
            pattern="static" if is_base else "circular",
            is_base_station=is_base,
            device_number=str(i+1)
        )
        
        logger.info(f"已添加RTK设备: ID={device_id}, IP={ip_address}, 基站={is_base}")
    
    # 启动所有设备
    simulator.start_all()
    logger.info(f"已启动所有RTK设备 ({args.devices}个), 目标: {args.target}:{args.port}")
    
    try:
        # 主循环
        while True:
            # 显示状态
            devices = simulator.get_all_devices()
            logger.info("-" * 50)
            logger.info(f"当前正在模拟 {len(devices)} 个RTK设备:")
            
            for device_id, device in devices.items():
                status = "运行中" if device["running"] else "已停止"
                pos = device["position"]
                logger.info(f"设备: {device_id} ({device['ip']}), 状态: {status}, 位置: E={pos['e']:.3f}, N={pos['n']:.3f}, U={pos['u']:.3f}")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止...")
    finally:
        # 停止所有设备
        simulator.stop_all()
        logger.info("已停止所有RTK设备")

if __name__ == "__main__":
    main() 