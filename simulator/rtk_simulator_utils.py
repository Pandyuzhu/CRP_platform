#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTK模拟器工具函数
"""

import math
import struct
import random
import socket
from typing import Tuple, List, Dict, Optional

# WGS-84常量
WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi

def geodetic_to_ecef(lat_deg: float, lon_deg: float, h: float) -> Tuple[float, float, float]:
    """
    将大地坐标(纬度,经度,高度)转换为ECEF(地心地固坐标系)坐标
    
    Args:
        lat_deg: 纬度(度)
        lon_deg: 经度(度)
        h: 高度(米)
        
    Returns:
        (x, y, z): ECEF坐标(米)
    """
    lat = lat_deg * DEG_TO_RAD
    lon = lon_deg * DEG_TO_RAD
    a = WGS84_A
    e2 = WGS84_E2
    
    N = a / math.sqrt(1 - e2 * math.sin(lat) * math.sin(lat))
    x = (N + h) * math.cos(lat) * math.cos(lon)
    y = (N + h) * math.cos(lat) * math.sin(lon)
    z = (N * (1 - e2) + h) * math.sin(lat)
    
    return (x, y, z)

def ecef_to_geodetic(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    将ECEF坐标转换为大地坐标
    
    Args:
        x, y, z: ECEF坐标(米)
        
    Returns:
        (lat_deg, lon_deg, h): 纬度(度), 经度(度), 高度(米)
    """
    a = WGS84_A
    e2 = WGS84_E2
    b = a * math.sqrt(1 - e2)
    ep2 = (a**2 - b**2) / b**2
    
    # 计算经度
    lon = math.atan2(y, x)
    
    # 初始化
    p = math.sqrt(x**2 + y**2)
    lat = math.atan2(z, p * (1 - e2))
    h = 0
    
    # 迭代计算纬度和高度
    for _ in range(5):  # 通常5次迭代足够
        N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
        h = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1 - e2 * N / (N + h)))
    
    return (lat * RAD_TO_DEG, lon * RAD_TO_DEG, h)

def ecef_to_enu(x: float, y: float, z: float, 
                x0: float, y0: float, z0: float,
                lat0_rad: float, lon0_rad: float) -> Tuple[float, float, float]:
    """
    将ECEF坐标转换为ENU(东-北-上)坐标
    
    Args:
        x, y, z: ECEF坐标(米)
        x0, y0, z0: 参考点ECEF坐标(米)
        lat0_rad: 参考点纬度(弧度)
        lon0_rad: 参考点经度(弧度)
        
    Returns:
        (e, n, u): ENU坐标(米)
    """
    dx = x - x0
    dy = y - y0
    dz = z - z0
    
    sin_lat = math.sin(lat0_rad)
    cos_lat = math.cos(lat0_rad)
    sin_lon = math.sin(lon0_rad)
    cos_lon = math.cos(lon0_rad)
    
    e = -sin_lon * dx + cos_lon * dy
    n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    
    return (e, n, u)

def enu_to_ecef(e: float, n: float, u: float,
                x0: float, y0: float, z0: float,
                lat0_rad: float, lon0_rad: float) -> Tuple[float, float, float]:
    """
    将ENU坐标转换为ECEF坐标
    
    Args:
        e, n, u: ENU坐标(米)
        x0, y0, z0: 参考点ECEF坐标(米)
        lat0_rad: 参考点纬度(弧度)
        lon0_rad: 参考点经度(弧度)
        
    Returns:
        (x, y, z): ECEF坐标(米)
    """
    sin_lat = math.sin(lat0_rad)
    cos_lat = math.cos(lat0_rad)
    sin_lon = math.sin(lon0_rad)
    cos_lon = math.cos(lon0_rad)
    
    dx = -sin_lon * e - sin_lat * cos_lon * n + cos_lat * cos_lon * u
    dy = cos_lon * e - sin_lat * sin_lon * n + cos_lat * sin_lon * u
    dz = cos_lat * n + sin_lat * u
    
    x = x0 + dx
    y = y0 + dy
    z = z0 + dz
    
    return (x, y, z)

def generate_gga_sentence(lat_deg: float, lon_deg: float, alt: float, 
                          quality: int = 4, num_sats: int = 12) -> str:
    """
    生成NMEA GGA语句
    
    Args:
        lat_deg: 纬度(度)
        lon_deg: 经度(度)
        alt: 高度(米)
        quality: 定位质量(0=无效,1=GPS,2=DGPS,4=RTK固定,5=RTK浮点)
        num_sats: 卫星数量
        
    Returns:
        GGA语句
    """
    # 将纬度转为NMEA格式 (ddmm.mmmmm)
    lat_abs = abs(lat_deg)
    lat_deg_int = int(lat_abs)
    lat_min = (lat_abs - lat_deg_int) * 60
    lat_str = f"{lat_deg_int:02d}{lat_min:09.6f}"
    lat_dir = "N" if lat_deg >= 0 else "S"
    
    # 将经度转为NMEA格式 (dddmm.mmmmm)
    lon_abs = abs(lon_deg)
    lon_deg_int = int(lon_abs)
    lon_min = (lon_abs - lon_deg_int) * 60
    lon_str = f"{lon_deg_int:03d}{lon_min:09.6f}"
    lon_dir = "E" if lon_deg >= 0 else "W"
    
    # 当前时间
    import time
    gmt = time.gmtime()
    hours = gmt.tm_hour
    minutes = gmt.tm_min
    seconds = gmt.tm_sec
    time_str = f"{hours:02d}{minutes:02d}{seconds:02d}"
    
    # 构造GGA语句
    gga = f"$GNGGA,{time_str},{lat_str},{lat_dir},{lon_str},{lon_dir},{quality},{num_sats:02d},1.0,{alt:.3f},M,0.0,M,,"
    
    # 计算校验和
    checksum = 0
    for char in gga[1:]:  # 跳过$符号
        checksum ^= ord(char)
    
    # 添加校验和并返回
    return f"{gga}*{checksum:02X}\r\n"

def create_udp_packet(timestamp_ms: int, enu: Tuple[float, float, float]) -> bytes:
    """
    创建UDP数据包，与ESP32代码兼容
    
    Args:
        timestamp_ms: 时间戳(毫秒)
        enu: (e, n, u)坐标(米)
        
    Returns:
        UDP数据包
    """
    packet = bytearray(16)
    
    # 写入时间戳（4字节，uint32）
    struct.pack_into('<I', packet, 0, timestamp_ms)
    
    # 写入ENU坐标（每个4字节，float）
    struct.pack_into('<f', packet, 4, enu[0])
    struct.pack_into('<f', packet, 8, enu[1])
    struct.pack_into('<f', packet, 12, enu[2])
    
    return packet

def get_local_ip_addresses() -> List[str]:
    """
    获取本机所有IP地址
    
    Returns:
        IP地址列表
    """
    ip_list = []
    
    try:
        # 获取所有网络接口
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
    except:
        # 如果失败，至少添加回环地址
        ip_list = ["127.0.0.1"]
    
    # 确保列表中有回环地址
    if "127.0.0.1" not in ip_list:
        ip_list.append("127.0.0.1")
    
    return ip_list 