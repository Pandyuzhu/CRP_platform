"""
视频流处理模块 - 提供VideoCamera类用于摄像头操作
"""

import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class VideoCamera:
    """处理摄像头视频流的类"""
    
    def __init__(self, camera_index=0):
        """初始化VideoCamera类
        
        Args:
            camera_index (int): 摄像头索引，默认为0（通常是第一个摄像头）
        """
        self.camera_index = camera_index
        self.is_active = False
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        
        # 尝试连接摄像头
        self.try_connect_camera()
    
    def try_connect_camera(self):
        """尝试连接摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.warning(f"无法打开摄像头 {self.camera_index}")
                self.is_active = False
                return False
            
            logger.info(f"成功连接摄像头 {self.camera_index}")
            self.is_active = True
            return True
        except Exception as e:
            logger.error(f"连接摄像头时出错: {e}")
            self.is_active = False
            return False
    
    def get_frame(self):
        """获取当前帧
        
        Returns:
            numpy.ndarray: 当前摄像头帧，如果摄像头未连接则返回None
        """
        if not self.is_active or self.cap is None:
            return None
        
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                self.is_active = False
                return None
            
            return frame
    
    def release(self):
        """释放摄像头资源"""
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                self.is_active = False
                logger.info(f"已释放摄像头 {self.camera_index}")
    
    def __del__(self):
        """析构函数，确保释放资源"""
        self.release() 