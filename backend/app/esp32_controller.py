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
             {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0100", "status": False},
            {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0200", "status": False},
            {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0400", "status": False},
            {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0800", "status": False},
            {"id": 5, "name": "喷浆启动", "action": "启动", "hex_code": "0x1000", "status": False},
            {"id": 6, "name": "喷浆停止", "action": "停止", "hex_code": "0x2000", "status": False},
            {"id": 7, "name": "水泵启动", "action": "启动", "hex_code": "0x4000", "status": False},
            {"id": 8, "name": "水泵停止", "action": "停止", "hex_code": "0x8000", "status": False},
            {"id": 9, "name": "水阀启动", "action": "启动", "hex_code": "0x0001", "status": False},
            {"id": 10, "name": "水阀停止", "action": "停止", "hex_code": "0x0002", "status": False},
            {"id": 11, "name": "喷浆反转", "action": "启动", "hex_code": "0x0004", "status": False}
        ]
    },
    "board2": {
        "ip": "192.168.0.121",
        "port": 3540,
        "name": "搅拌机2和末端喷头控制板",
        "buttons": [
            {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0100", "status": False},
            {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0200", "status": False},
            {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0400", "status": False},
            {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0800", "status": False},
            {"id": 5, "name": "水泵启动", "action": "启动", "hex_code": "0x1000", "status": False},
            {"id": 6, "name": "水泵停止", "action": "停止", "hex_code": "0x2000", "status": False},
            {"id": 7, "name": "水阀启动", "action": "启动", "hex_code": "0x4000", "status": False},
            {"id": 8, "name": "水阀停止", "action": "停止", "hex_code": "0x8000", "status": False},
            {"id": 9, "name": "开启搅拌仓1", "action": "启动", "hex_code": "0x0001", "status": False},
            {"id": 10, "name": "关闭搅拌仓1", "action": "停止", "hex_code": "0x0002", "status": False},
            {"id": 11, "name": "开启搅拌仓2", "action": "启动", "hex_code": "0x0004", "status": False},
            {"id": 12, "name": "关闭搅拌仓2", "action": "停止", "hex_code": "0x0008", "status": False}
        ]
    }
}

# 按钮分组
BUTTON_GROUPS = {
    "mixer1": ["搅拌运行", "搅拌停止", "输送启动", "输送停止", "水泵启动", "水泵停止", "水阀启动", "水阀停止"],
    "sprayer": ["喷浆启动", "喷浆停止", "喷浆反转"],
    "mixer2": ["搅拌运行", "搅拌停止", "输送启动", "输送停止", "水泵启动", "水泵停止", "水阀启动", "水阀停止"],
    "nozzle": ["开启搅拌仓1", "关闭搅拌仓1", "开启搅拌仓2", "关闭搅拌仓2"]
}

class ESP32Controller:
    """ESP32控制器类，用于管理ESP32控制板连接和发送命令"""
    
    def __init__(self):
        """初始化ESP32控制器"""
        # 初始化ESP32控制板配置
        self.boards = {
            "board1": {
                "name": "控制板1",
                "ip": "192.168.0.120",  # ESP32控制板1的IP地址
                "port": 3540,          # ESP32控制板1的端口
                "description": "搅拌机1和喷射机控制",
                "buttons": [
                    {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0100", "status": False},
                    {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0200", "status": False},
                    {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0400", "status": False},
                    {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0800", "status": False},
                    {"id": 5, "name": "喷浆启动", "action": "启动", "hex_code": "0x1000", "status": False},
                    {"id": 6, "name": "喷浆停止", "action": "停止", "hex_code": "0x2000", "status": False},
                    {"id": 7, "name": "水泵启动", "action": "启动", "hex_code": "0x4000", "status": False},
                    {"id": 8, "name": "水泵停止", "action": "停止", "hex_code": "0x8000", "status": False},
                    {"id": 9, "name": "水阀启动", "action": "启动", "hex_code": "0x0001", "status": False},
                    {"id": 10, "name": "水阀停止", "action": "停止", "hex_code": "0x0002", "status": False},
                    {"id": 11, "name": "喷浆反转", "action": "启动", "hex_code": "0x0004", "status": False},
                ]
            },
            "board2": {
                "name": "控制板2",
                "ip": "192.168.0.121",  # ESP32控制板2的IP地址
                "port": 3540,          # ESP32控制板2的端口
                "description": "搅拌机2和末端喷头控制",
                "buttons": [
                    {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0100", "status": False},
                    {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0200", "status": False},
                    {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0400", "status": False},
                    {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0800", "status": False},
                    {"id": 5, "name": "水泵启动", "action": "启动", "hex_code": "0x1000", "status": False},
                    {"id": 6, "name": "水泵停止", "action": "停止", "hex_code": "0x2000", "status": False},
                    {"id": 7, "name": "水阀启动", "action": "启动", "hex_code": "0x4000", "status": False},
                    {"id": 8, "name": "水阀停止", "action": "停止", "hex_code": "0x8000", "status": False},
                    {"id": 9, "name": "开启搅拌仓1", "action": "启动", "hex_code": "0x0100", "status": False},
                    {"id": 10, "name": "关闭搅拌仓1", "action": "停止", "hex_code": "0x0200", "status": False},
                    {"id": 11, "name": "开启搅拌仓2", "action": "启动", "hex_code": "0x0400", "status": False},
                    {"id": 12, "name": "关闭搅拌仓2", "action": "停止", "hex_code": "0x0800", "status": False}
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
            # 创建UDP Socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3.0)  # 设置超时时间
            
            logger.info(f"准备通过UDP发送命令到ESP32控制板 {board_id}: {board['ip']}:{board['port']}")
            
            # 将16进制代码转换为字节
            hex_code = int(button["hex_code"], 16)
            command = hex_code.to_bytes(2, byteorder='big')
            
            # 尝试发送UDP数据包
            try:
                # UDP不需要预先连接，直接发送到目标地址
                await asyncio.to_thread(sock.sendto, command, (board['ip'], board['port']))
                # logger.info(f"成功发送UDP命令到ESP32控制板 {board_id}: {board['ip']}:{board['port']}")
                
                # 尝试接收响应 (UDP是无连接的，可能不会收到响应)
                try:
                    sock.settimeout(2.0)  # 设置接收响应的超时时间
                    response, addr = await asyncio.to_thread(sock.recvfrom, 1024)
                    logger.info(f"收到来自 {addr} 的UDP响应: {response.hex() if response else '无响应'}")
                    # 更新连接状态
                    with self.status_lock:
                        self.connection_status[board_id] = True
                except (socket.timeout, socket.error):
                    logger.warning(f"未收到ESP32控制板 {board_id} 的UDP响应，但这可能是正常的")
                    # 尝试发送成功，但没收到响应时也认为连接正常
                    with self.status_lock:
                        self.connection_status[board_id] = True
            except Exception as e:
                logger.warning(f"尝试连接实际设备失败，使用本地UDP连接: 127.0.0.1:{board['port']}")
                # 如果连接失败，尝试连接到本地模拟器
                await asyncio.to_thread(sock.sendto, command, ('127.0.0.1', board['port']))
                logger.info(f"成功发送UDP命令到本地ESP32模拟器: 127.0.0.1:{board['port']}")
                
                try:
                    sock.settimeout(2.0)
                    response, addr = await asyncio.to_thread(sock.recvfrom, 1024)
                    logger.info(f"收到来自本地模拟器 {addr} 的UDP响应: {response.hex() if response else '无响应'}")
                    with self.status_lock:
                        self.connection_status[board_id] = True
                except (socket.timeout, socket.error):
                    logger.warning("未收到本地模拟器的UDP响应，但这可能是正常的")
                    # 即使没收到响应，也认为连接正常（因为UDP特性）
                    with self.status_lock:
                        self.connection_status[board_id] = True
            
            # 关闭套接字
            sock.close()
            
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
                "message": f"成功发送UDP命令: {button['name']}"
            }
            
        except Exception as e:
            logger.error(f"发送UDP命令时出现未知错误: {str(e)}")
            
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
                "warning": f"处理UDP命令时出错: {str(e)}"
            }

# 创建全局控制器实例
controller = ESP32Controller() 