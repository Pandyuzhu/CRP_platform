import socket
import logging
import asyncio
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiftCarController:
    """登高车控制器类，用于发送UDP命令控制登高车"""
    
    def __init__(self):
        """初始化登高车控制器"""
        # 初始化登高车配置
        self.config = {
            "ip": "127.0.0.1",  # 登高车ESP32控制板IP (使用本地IP确保与模拟器连接)
            "port": 5300,        # 登高车ESP32控制板端口
            "description": "登高车控制",
            "joint_states": {
                "joint1": 0,  # 0=停止，1=伸展，2=屈曲
                "joint2": 0,  # 0=停止，1=伸展，2=屈曲
                "joint3": 0   # 0=停止，1=伸展，2=屈曲
            }
        }
        
        # 按钮配置
        self.buttons = [
            {"id": 1, "name": "关节1伸展", "action": "伸展", "joint": "joint1", "value": 1, "status": False},
            {"id": 2, "name": "关节1停止", "action": "停止", "joint": "joint1", "value": 0, "status": False},
            {"id": 3, "name": "关节1屈曲", "action": "屈曲", "joint": "joint1", "value": 2, "status": False},
            
            {"id": 4, "name": "关节2伸展", "action": "伸展", "joint": "joint2", "value": 1, "status": False},
            {"id": 5, "name": "关节2停止", "action": "停止", "joint": "joint2", "value": 0, "status": False},
            {"id": 6, "name": "关节2屈曲", "action": "屈曲", "joint": "joint2", "value": 2, "status": False},
            
            {"id": 7, "name": "关节3伸展", "action": "伸展", "joint": "joint3", "value": 1, "status": False},
            {"id": 8, "name": "关节3停止", "action": "停止", "joint": "joint3", "value": 0, "status": False},
            {"id": 9, "name": "关节3屈曲", "action": "屈曲", "joint": "joint3", "value": 2, "status": False},
            
            {"id": 10, "name": "全部停止", "action": "停止", "joint": "all", "value": 0, "status": False}
        ]
        
        # 创建UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def get_info(self):
        """获取登高车信息"""
        return {
            "config": self.config,
            "buttons": self.buttons
        }
    
    def update_button_status(self, button_id: int, status: bool):
        """更新按钮状态"""
        for button in self.buttons:
            if button["id"] == button_id:
                button["status"] = status
                break
    
    async def send_command(self, button_id: int):
        """发送控制命令到登高车ESP32控制板"""
        button = None
        
        # 查找对应的按钮
        for btn in self.buttons:
            if btn["id"] == button_id:
                button = btn
                break
        
        if not button:
            return {"error": "无效的按钮ID"}
        
        try:
            # 如果是全部停止按钮，则停止所有关节
            if button["joint"] == "all":
                self.config["joint_states"]["joint1"] = 0
                self.config["joint_states"]["joint2"] = 0
                self.config["joint_states"]["joint3"] = 0
                
                # 更新所有停止按钮状态
                for btn in self.buttons:
                    if btn["action"] == "停止":
                        self.update_button_status(btn["id"], True)
                    else:
                        self.update_button_status(btn["id"], False)
            else:
                # 更新关节状态
                self.config["joint_states"][button["joint"]] = button["value"]
                
                # 更新按钮状态
                # 只能有一个关节动作被激活，其他的设为false
                for btn in self.buttons:
                    if btn["joint"] == button["joint"]:
                        self.update_button_status(btn["id"], btn["id"] == button_id)
            
            # 构建4字节命令
            command = bytearray(4)
            command[0] = 1  # 使能标志，1表示启用
            command[1] = self.config["joint_states"]["joint1"]
            command[2] = self.config["joint_states"]["joint2"]
            command[3] = self.config["joint_states"]["joint3"]
            
            logger.info(f"发送命令到登高车: {list(command)}")
            
            # 发送UDP数据包
            try:
                # 尝试发送到配置的IP
                logger.info(f"尝试连接到登高车: {self.config['ip']}:{self.config['port']}")
                await asyncio.to_thread(
                    self.sock.sendto, 
                    command, 
                    (self.config["ip"], self.config["port"])
                )
                logger.info(f"成功发送命令到登高车: {self.config['ip']}:{self.config['port']}")
            except Exception as e:
                # 如果失败，尝试连接到本地模拟器
                logger.warning(f"连接真实设备失败，尝试连接本地模拟器: 127.0.0.1:{self.config['port']}")
                try:
                    await asyncio.to_thread(
                        self.sock.sendto, 
                        command, 
                        ('127.0.0.1', self.config["port"])
                    )
                    logger.info(f"成功发送命令到本地登高车模拟器")
                except Exception as inner_e:
                    logger.error(f"连接本地模拟器也失败: {str(inner_e)}")
                    return {
                        "success": False, 
                        "message": f"发送命令失败: 无法连接到设备或模拟器"
                    }
            
            return {
                "success": True,
                "message": f"成功发送命令: {button['name']}",
                "command": list(command)
            }
            
        except Exception as e:
            logger.error(f"发送命令时出现错误: {str(e)}")
            return {
                "success": False, 
                "message": f"发送命令失败: {str(e)}"
            }

# 创建全局控制器实例
lift_car_controller = LiftCarController() 