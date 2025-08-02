"""
机械臂HLS视频流服务模块
提供机械臂摄像头状态监控和流信息管理
"""

import logging
import requests
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ArmStreamingService:
    """机械臂HLS流服务类"""
    
    def __init__(self, stream_url: str = "http://192.168.0.51:80/hlsram/live0/index.m3u8"):
        """初始化机械臂流服务
        
        Args:
            stream_url (str): HLS流地址
        """
        self.stream_url = stream_url
        self.is_connected = True  # 默认为连接状态，避免初始显示为离线
        self.last_check_time = 0
        self.check_interval = 60  # 检查间隔增加到60秒，大幅减少频繁检查
        self.connection_timeout = 5  # 连接超时设为5秒
        
    def check_camera_connection(self) -> bool:
        """检查机械臂摄像头连接状态
        
        Returns:
            bool: 摄像头是否连接
        """
        current_time = time.time()
        
        # 避免频繁检查
        if current_time - self.last_check_time < self.check_interval:
            return self.is_connected
        
        self.last_check_time = current_time
        
        try:
            # 使用GET请求替代HEAD请求，添加stream=True避免下载完整内容
            response = requests.get(
                self.stream_url, 
                timeout=self.connection_timeout,
                allow_redirects=True,
                stream=True  # 不下载完整内容，只检查连接
            )
            
            # 检查响应状态
            if response.status_code == 200:
                if not self.is_connected:  # 只在状态改变时记录日志
                    logger.info(f"机械臂摄像头连接恢复正常: {self.stream_url}")
                self.is_connected = True
            else:
                if self.is_connected:  # 只在状态改变时记录日志
                    logger.warning(f"机械臂摄像头响应异常: {response.status_code}")
                self.is_connected = False
                
            # 关闭响应流，释放资源
            response.close()
                
        except requests.exceptions.Timeout:
            # 超时不算严重错误，可能是网络延迟，保持连接状态不变
            logger.debug(f"机械臂摄像头连接超时，保持当前状态")
            # 不改变连接状态，保持上一次的状态
            
        except requests.exceptions.ConnectionError:
            # 连接错误也不立即标记为离线，可能是网络问题
            logger.debug(f"机械臂摄像头连接错误，保持当前状态")
            # 保持当前状态不变
            
        except requests.exceptions.RequestException as e:
            # 其他请求异常，降低日志级别
            logger.debug(f"机械臂摄像头连接检查异常: {e}")
            # 保持当前状态不变，不设为False
            
        except Exception as e:
            logger.debug(f"机械臂摄像头状态检查出错: {e}")
            # 保持当前状态不变
        
        return self.is_connected
    
    def get_stream_info(self) -> Dict[str, Any]:
        """获取机械臂流信息
        
        Returns:
            Dict[str, Any]: 流信息字典
        """
        camera_connected = self.check_camera_connection()
        
        return {
            "camera_connected": camera_connected,
            "stream_url": self.stream_url,
            "stream_type": "HLS",
            "protocol": "HTTP Live Streaming",
            "last_check": self.last_check_time,
            "check_interval": self.check_interval,
            "low_latency_enabled": True,
            "timestamp": time.time()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取机械臂服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        # 检查连接状态，但不强制更新
        camera_connected = self.check_camera_connection()
        
        return {
            "service_name": "ArmStreamingService",
            "stream_url": self.stream_url,
            "camera_connected": camera_connected,
            "service_active": True,
            "check_interval": self.check_interval,
            "note": "Camera status based on periodic checks, may not reflect real-time status",
            "timestamp": time.time()
        }
    
    def update_connection_status(self, is_connected: bool):
        """允许外部更新连接状态（例如基于前端反馈）
        
        Args:
            is_connected (bool): 连接状态
        """
        if self.is_connected != is_connected:
            logger.info(f"机械臂摄像头状态更新: {'连接' if is_connected else '断开'}")
            self.is_connected = is_connected

# 创建全局实例
arm_streaming_service = ArmStreamingService() 