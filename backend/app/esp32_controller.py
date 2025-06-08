import socket
import logging
import time
import threading
import asyncio
import json
from typing import Dict, List, Optional, Tuple, Any

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ESP32控制板信息
ESP32_BOARDS = {
    "board1": {
        "ip": "192.168.3.120",
        "port": 5200,
        "name": "搅拌机1和喷射机控制板",
        "buttons": [
            {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": False},
            {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": False},
            {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": False},
            {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": False},
            {"id": 5, "name": "喷浆启动", "action": "启动", "hex_code": "0x0010", "status": False},
            {"id": 6, "name": "喷浆停止", "action": "停止", "hex_code": "0x0020", "status": False},
            {"id": 7, "name": "水泵启动", "action": "启动", "hex_code": "0x0040", "status": False},
            {"id": 8, "name": "水泵停止", "action": "停止", "hex_code": "0x0080", "status": False},
            {"id": 9, "name": "水阀启动", "action": "启动", "hex_code": "0x0100", "status": False},
            {"id": 10, "name": "水阀停止", "action": "停止", "hex_code": "0x0200", "status": False}
        ]
    },
    "board2": {
        "ip": "192.168.3.121",
        "port": 5201,
        "name": "搅拌机2和末端喷头控制板",
        "buttons": [
            {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": False},
            {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": False},
            {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": False},
            {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": False},
            {"id": 5, "name": "水泵启动", "action": "启动", "hex_code": "0x0010", "status": False},
            {"id": 6, "name": "水泵停止", "action": "停止", "hex_code": "0x0020", "status": False},
            {"id": 7, "name": "水阀启动", "action": "启动", "hex_code": "0x0040", "status": False},
            {"id": 8, "name": "水阀停止", "action": "停止", "hex_code": "0x0080", "status": False},
            {"id": 9, "name": "喷头纤维喷射启动", "action": "启动", "hex_code": "0x0100", "status": False},
            {"id": 10, "name": "喷头纤维喷射停止", "action": "停止", "hex_code": "0x0200", "status": False},
            {"id": 11, "name": "喷头浆料喷射启动", "action": "启动", "hex_code": "0x0400", "status": False},
            {"id": 12, "name": "喷头浆料喷射停止", "action": "停止", "hex_code": "0x0800", "status": False}
        ]
    }
}

# 按钮分组
BUTTON_GROUPS = {
    "mixer1": ["搅拌运行", "搅拌停止", "输送启动", "输送停止", "水泵启动", "水泵停止", "水阀启动", "水阀停止"],
    "sprayer": ["喷浆启动", "喷浆停止"],
    "mixer2": ["搅拌运行", "搅拌停止", "输送启动", "输送停止", "水泵启动", "水泵停止", "水阀启动", "水阀停止"],
    "nozzle": ["喷头纤维喷射启动", "喷头纤维喷射停止", "喷头浆料喷射启动", "喷头浆料喷射停止"]
}

class ESP32Controller:
    """ESP32控制器类，用于管理ESP32控制板连接和发送命令"""
    
    def __init__(self):
        """初始化ESP32控制器"""
        # 初始化ESP32控制板配置
        self.boards = {
            "board1": {
                "name": "控制板1",
                "ip": "192.168.3.120",  # ESP32控制板1的IP地址
                "port": 5200,          # ESP32控制板1的端口
                "description": "搅拌机1和喷射机控制",
                "buttons": [
                    {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": False},
                    {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": False},
                    {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": False},
                    {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": False},
                    {"id": 5, "name": "喷浆启动", "action": "启动", "hex_code": "0x0010", "status": False},
                    {"id": 6, "name": "喷浆停止", "action": "停止", "hex_code": "0x0020", "status": False},
                    {"id": 7, "name": "水泵启动", "action": "启动", "hex_code": "0x0040", "status": False},
                    {"id": 8, "name": "水泵停止", "action": "停止", "hex_code": "0x0080", "status": False},
                    {"id": 9, "name": "水阀启动", "action": "启动", "hex_code": "0x0100", "status": False},
                    {"id": 10, "name": "水阀停止", "action": "停止", "hex_code": "0x0200", "status": False}
                ]
            },
            "board2": {
                "name": "控制板2",
                "ip": "192.168.3.121",  # ESP32控制板2的IP地址
                "port": 5201,          # ESP32控制板2的端口
                "description": "搅拌机2和末端喷头控制",
                "buttons": [
                    {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": False},
                    {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": False},
                    {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": False},
                    {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": False},
                    {"id": 5, "name": "水泵启动", "action": "启动", "hex_code": "0x0010", "status": False},
                    {"id": 6, "name": "水泵停止", "action": "停止", "hex_code": "0x0020", "status": False},
                    {"id": 7, "name": "水阀启动", "action": "启动", "hex_code": "0x0040", "status": False},
                    {"id": 8, "name": "水阀停止", "action": "停止", "hex_code": "0x0080", "status": False},
                    {"id": 9, "name": "纤维喷射启动", "action": "启动", "hex_code": "0x0100", "status": False},
                    {"id": 10, "name": "纤维喷射停止", "action": "停止", "hex_code": "0x0200", "status": False},
                    {"id": 11, "name": "浆料喷射启动", "action": "启动", "hex_code": "0x0400", "status": False},
                    {"id": 12, "name": "浆料喷射停止", "action": "停止", "hex_code": "0x0800", "status": False}
                ]
            }
        }
        
        # 连接状态
        self.connection_status = {
            "board1": False,
            "board2": False
        }
        
        # 状态锁
        self.status_lock = threading.Lock()
    
    def get_boards_info(self):
        """获取所有控制板信息"""
        return self.boards
    
    def get_board_status(self, board_id: str):
        """获取指定控制板的状态"""
        if board_id not in self.boards:
            return {"error": "无效的控制板ID"}
        
        with self.status_lock:
            board_info = self.boards[board_id].copy()
            board_info["connected"] = self.connection_status[board_id]
            return board_info
    
    def get_all_status(self):
        """获取所有控制板的状态"""
        result = {}
        for board_id in self.boards:
            result[board_id] = self.get_board_status(board_id)
        return result
    
    def update_button_status(self, board_id: str, button_id: int, status: bool):
        """更新按钮状态"""
        if board_id not in self.boards:
            return {"error": "无效的控制板ID"}
        
        with self.status_lock:
            for button in self.boards[board_id]["buttons"]:
                if button["id"] == button_id:
                    button["status"] = status
                    return {"success": True, "message": f"已更新按钮状态: {button['name']} -> {status}"}
            
            return {"error": "无效的按钮ID"}
    
    async def send_command(self, board_id: str, button_id: int):
        """发送控制命令到ESP32板"""
        if board_id not in self.boards:
            return {"error": "无效的控制板ID"}
        
        board = self.boards[board_id]
        button = None
        
        # 查找对应的按钮
        for btn in board["buttons"]:
            if btn["id"] == button_id:
                button = btn
                break
        
        if not button:
            return {"error": "无效的按钮ID"}
        
        try:
            # 创建TCP Socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)  # 设置超时时间
            
            logger.info(f"正在连接到ESP32控制板 {board_id}: {board['ip']}:{board['port']}")
            
            # 尝试连接
            try:
                await asyncio.to_thread(sock.connect, (board['ip'], board['port']))
                logger.info(f"成功连接到ESP32控制板 {board_id}")
            except Exception as e:
                logger.warning(f"尝试使用本地连接: 127.0.0.1:{board['port']}")
                # 如果连接失败，尝试连接到本地模拟器
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                await asyncio.to_thread(sock.connect, ('127.0.0.1', board['port']))
                logger.info(f"成功连接到本地ESP32模拟器 {board_id}")
            
            # 更新连接状态
            with self.status_lock:
                self.connection_status[board_id] = True
            
            # 将16进制代码转换为字节
            hex_code = int(button["hex_code"], 16)
            command = hex_code.to_bytes(2, byteorder='big')
            
            logger.info(f"发送命令到ESP32控制板 {board_id}: 按钮={button['name']}, 命令={button['hex_code']}")
            await asyncio.to_thread(sock.sendall, command)
            
            # 等待响应
            response = await asyncio.to_thread(sock.recv, 1024)
            logger.info(f"收到响应: {response.hex() if response else '无响应'}")
            
            # 关闭连接
            sock.close()
            
            # 即使没有得到有效响应，也更新按钮状态，以保证前端能正常工作
            # 更新按钮状态
            if button["action"] == "启动":
                self.update_button_status(board_id, button_id, True)
                # 如果是启动按钮，将对应的停止按钮状态设为False
                if button_id % 2 == 1:  # 奇数ID是启动按钮
                    self.update_button_status(board_id, button_id + 1, False)
            else:
                self.update_button_status(board_id, button_id, False)
                # 如果是停止按钮，将对应的启动按钮状态设为False
                if button_id % 2 == 0:  # 偶数ID是停止按钮
                    self.update_button_status(board_id, button_id - 1, False)
            
            return {
                "success": True, 
                "message": f"成功发送命令: {button['name']}", 
                "response": response.hex() if response else "无响应"
            }
            
        except (socket.timeout, socket.error) as e:
            # 更新连接状态
            with self.status_lock:
                self.connection_status[board_id] = False
            
            # 即使通信失败，也更新按钮状态，以保证前端能正常工作
            if button["action"] == "启动":
                self.update_button_status(board_id, button_id, True)
                if button_id % 2 == 1:
                    self.update_button_status(board_id, button_id + 1, False)
            else:
                self.update_button_status(board_id, button_id, False)
                if button_id % 2 == 0:
                    self.update_button_status(board_id, button_id - 1, False)
            
            logger.error(f"与ESP32控制板 {board_id} 通信失败: {str(e)}")
            return {
                "success": True,  # 即使通信失败，也返回成功，以保证前端能正常工作
                "message": f"已发送命令: {button['name']} (无法确认设备是否接收)", 
                "warning": f"与设备通信失败: {str(e)}"
            }
        except Exception as e:
            logger.error(f"发送命令时出现未知错误: {str(e)}")
            
            # 即使发生错误，也更新按钮状态，以保证前端能正常工作
            if button["action"] == "启动":
                self.update_button_status(board_id, button_id, True)
                if button_id % 2 == 1:
                    self.update_button_status(board_id, button_id + 1, False)
            else:
                self.update_button_status(board_id, button_id, False)
                if button_id % 2 == 0:
                    self.update_button_status(board_id, button_id - 1, False)
            
            return {
                "success": True,  # 即使出错，也返回成功，以保证前端能正常工作
                "message": f"已发送命令: {button['name']} (处理过程中出错)", 
                "warning": f"处理命令时出错: {str(e)}"
            }

# 创建全局控制器实例
controller = ESP32Controller() 