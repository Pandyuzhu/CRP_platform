import os
import cv2
import time
import asyncio
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import threading
import numpy as np
from . import zed_server
from app.esp32_controller import controller as esp32_controller
import logging
import atexit
import signal
from fastapi.responses import StreamingResponse
from app.video_streaming import VideoCamera
from app.lift_controller import lift_car_controller

# Initialize FastAPI app
app = FastAPI(title="Smart Construction Platform")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directory for storing video frames if it doesn't exist
os.makedirs("data/video_frames", exist_ok=True)

# Global variables for video streaming
frame_buffer = None
frame_lock = threading.Lock()
is_streaming = False
stream_info = {
    "fps": 0,
    "frame_count": 0,
    "start_time": None,
    "source_address": None,
    "resolution": "Unknown"
}

# 用于优雅关闭的事件标志
shutdown_event = threading.Event()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_app")

# 初始化视频相机
camera = None
try:
    camera = VideoCamera()
    logger.info("Camera initialized successfully")
except Exception as e:
    logger.error(f"Error initializing camera: {e}")

def receive_rtp_stream():
    """Receive RTP stream and update the global frame buffer"""
    global frame_buffer, is_streaming, stream_info
    
    print("开始接收RTP视频流...")
    # 初始化OpenCV的VideoCapture以接收RTP流
    # 使用udpsrc作为GStreamer管道
    gst_str = (
        "udpsrc port=5000 ! "
        "application/x-rtp,media=video,payload=96,clock-rate=90000,encoding-name=H264 ! "
        "rtph264depay ! h264parse ! avdec_h264 ! "
        "videoconvert ! appsink"
    )
    cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    
    # 初始化时间和FPS计算
    stream_info["start_time"] = time.time()
    frame_time = time.time()
    fps_update_time = time.time()
    
    try:
        while not shutdown_event.is_set():  # 检查关闭事件
            ret, frame = cap.read()
            
            if not ret:
                # 如果无法获取帧，等待一段时间然后继续尝试
                time.sleep(0.1)
                continue
            
            # 成功接收到帧，设置流状态为活跃
            is_streaming = True
            
            # 计算FPS
            current_time = time.time()
            if current_time - frame_time > 0:
                instantaneous_fps = 1.0 / (current_time - frame_time)
                
                # 平滑FPS计算，每秒更新一次
                if current_time - fps_update_time >= 1.0:
                    stream_info["fps"] = round(instantaneous_fps, 1)
                    fps_update_time = current_time
                    
                    # 打印流信息
                    if not shutdown_event.is_set():  # 只在非关闭状态下记录日志
                        logger.info(f"视频流信息 - FPS: {stream_info['fps']}, 帧数: {stream_info['frame_count']}")
            
            frame_time = current_time
            stream_info["frame_count"] += 1
            
            # 获取分辨率信息（只在第一帧时获取）
            if stream_info["resolution"] == "Unknown" and frame is not None:
                height, width = frame.shape[:2]
                stream_info["resolution"] = f"{width}x{height}"
            
            # 添加时间戳和信息到帧上
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"时间: {timestamp}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"FPS: {stream_info['fps']}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 更新全局帧缓冲区
            with frame_lock:
                frame_buffer = frame
            
    except Exception as e:
        if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
            logger.error(f"视频流接收错误: {e}")
        is_streaming = False
    finally:
        cap.release()
        if not shutdown_event.is_set():  # 只在非关闭状态下记录日志
            logger.info("RTP流接收已停止")
        is_streaming = False

def generate_frames():
    """Generate frames for HTTP streaming"""
    global frame_buffer
    
    while True:
        with frame_lock:
            if frame_buffer is not None:
                # Encode the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame_buffer)
                frame_bytes = buffer.tobytes()
                
                # Yield the frame for the HTTP response
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # If no frame is available, send a blank frame or error message
                blank_frame = create_blank_frame("等待视频流...")
                _, buffer = cv2.imencode('.jpg', blank_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control the frame rate
        time.sleep(0.033)  # ~30 FPS

def create_blank_frame(message="No video signal"):
    """Create a blank frame with error message when no video is available"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add a grid pattern for visual effect
    for i in range(0, 480, 40):
        cv2.line(frame, (0, i), (640, i), (0, 0, 80), 1)
    
    for i in range(0, 640, 40):
        cv2.line(frame, (i, 0), (i, 480), (0, 0, 80), 1)
    
    # Add text message
    cv2.putText(frame, message, (int(640/2) - 100, int(480/2)), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # Add timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp, (20, 460), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    return frame

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.client_connections = {}  # 用于跟踪每个客户端IP的连接数
        self.max_connections_per_client = 4  # 每个客户端最多允许4个WebSocket连接
        self.max_total_connections = 20  # 系统总共最多允许20个WebSocket连接

    async def connect(self, websocket: WebSocket):
        # 检查是否处于关闭状态
        if shutdown_event.is_set():
            await websocket.close(code=1001, reason="Server shutting down")
            return False
            
        # 获取客户端IP
        client_host = websocket.client.host
        
        # 检查总连接数是否超过限制
        if len(self.active_connections) >= self.max_total_connections:
            logger.warning(f"总连接数已达到上限 ({self.max_total_connections})，拒绝新连接")
            await websocket.close(code=1013, reason="Maximum connections reached")
            return False
        
        # 检查该客户端的连接数是否超过限制
        if client_host in self.client_connections and self.client_connections[client_host] >= self.max_connections_per_client:
            logger.warning(f"客户端 {client_host} 的连接数已达到上限 ({self.max_connections_per_client})，拒绝新连接")
            await websocket.close(code=1013, reason="Too many connections from this client")
            return False
            
        # 接受连接
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 更新客户端连接计数
        if client_host not in self.client_connections:
            self.client_connections[client_host] = 1
        else:
            self.client_connections[client_host] += 1
            
        logger.info(f"新的WebSocket连接，客户端IP: {client_host}，该客户端连接数: {self.client_connections[client_host]}，总连接数: {len(self.active_connections)}")
        return True

    def disconnect(self, websocket: WebSocket):
        # 获取客户端IP
        client_host = websocket.client.host if hasattr(websocket, 'client') else "unknown"
        
        # 从活跃连接列表中移除
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            # 更新客户端连接计数
            if client_host in self.client_connections:
                self.client_connections[client_host] -= 1
                if self.client_connections[client_host] <= 0:
                    del self.client_connections[client_host]
                    
            logger.info(f"WebSocket连接关闭，客户端IP: {client_host}，该客户端剩余连接数: {self.client_connections.get(client_host, 0)}，总连接数: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
    
    async def close_all_connections(self):
        """关闭所有活跃的WebSocket连接"""
        logger.info(f"正在关闭所有WebSocket连接，当前共有 {len(self.active_connections)} 个连接")
        for websocket in self.active_connections[:]:  # 使用副本进行迭代，避免在迭代时修改列表
            try:
                await websocket.close(code=1001, reason="Server shutting down")
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"关闭WebSocket连接时出错: {e}")
        
        # 清空连接计数
        self.client_connections.clear()
        logger.info("所有WebSocket连接已关闭")

manager = ConnectionManager()

# 启动ZED服务器
zed_server.init_zed_server()

# Start the RTP stream receiver in a separate thread
stream_thread = threading.Thread(target=receive_rtp_stream, daemon=True)
stream_thread.start()

@app.get("/")
async def get_index():
    return {"message": "Smart Construction Platform API is running"}

@app.get("/api/video_feed")
async def video_feed_api():
    """API Endpoint for HTTP video streaming"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/stream_status")
async def stream_status_api():
    """获取视频流状态API"""
    zed_connected = zed_server.is_zed_connected()
    
    if camera:
        return {
            "is_streaming": is_streaming,
            "fps": stream_info["fps"],
            "resolution": stream_info["resolution"],
            "frame_count": stream_info["frame_count"],
            "uptime": int(time.time() - stream_info["start_time"]) if stream_info["start_time"] else 0,
            "zed_connected": zed_connected,  # 添加ZED相机连接状态
            "stream_active": camera.is_active,
            "camera_index": camera.camera_index
        }
    else:
        return {
            "is_streaming": is_streaming,
            "fps": stream_info["fps"],
            "resolution": stream_info["resolution"],
            "frame_count": stream_info["frame_count"],
            "uptime": int(time.time() - stream_info["start_time"]) if stream_info["start_time"] else 0,
            "zed_connected": zed_connected,  # 添加ZED相机连接状态
            "stream_active": False,
            "camera_index": -1
        }

@app.websocket("/ws/video")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for video streaming"""
    # 尝试连接，如果达到限制则会返回False
    if not await manager.connect(websocket):
        return  # 连接被拒绝，直接返回
        
    try:
        while not shutdown_event.is_set():  # 检查关闭事件
            with frame_lock:
                if frame_buffer is not None and is_streaming:
                    # Encode the frame as JPEG with quality setting to control bandwidth
                    _, buffer = cv2.imencode('.jpg', frame_buffer, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_bytes = buffer.tobytes()
                    
                    # Send the frame through WebSocket
                    await websocket.send_bytes(frame_bytes)
                else:
                    # 不发送模拟帧，让前端显示离线状态
                    # 发送一个空的1x1像素的透明图片，这样前端会触发错误处理
                    empty_frame = np.zeros((1, 1, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', empty_frame)
                    frame_bytes = buffer.tobytes()
                    await websocket.send_bytes(frame_bytes)
            
            # Control the frame rate - adjust for network performance
            await asyncio.sleep(0.05)  # 20 FPS for WebSocket to reduce bandwidth
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
            logger.error(f"WebSocket错误: {e}")
    finally:
        manager.disconnect(websocket)

# 添加另一个路径以支持API前缀
@app.websocket("/api/ws/video")
async def websocket_endpoint_api(websocket: WebSocket):
    """WebSocket API endpoint for video streaming"""
    await websocket_endpoint(websocket)

# ZED相机WebSocket端点
@app.websocket("/ws/zed/rgb")
async def zed_rgb_endpoint(websocket: WebSocket):
    """ZED RGB视频流WebSocket端点"""
    # 尝试连接，如果达到限制则会返回False
    if not await manager.connect(websocket):
        return  # 连接被拒绝，直接返回
        
    try:
        # 添加超时机制，防止无限循环
        max_inactive_time = 60  # 最大不活跃时间（秒）
        start_time = time.time()
        
        while not shutdown_event.is_set():  # 检查关闭事件
            # 检查连接是否已超时
            if time.time() - start_time > max_inactive_time:
                logger.info(f"ZED RGB WebSocket连接超时，已断开")
                break
                
            with zed_server.rgb_frame_lock:
                if zed_server.rgb_frame is not None:
                    # 重置超时计时器
                    start_time = time.time()
                    
                    # 缩放图像以减少带宽
                    resized_frame = cv2.resize(zed_server.rgb_frame, (640, 360))
                    # 编码为JPEG
                    _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                    
                    # 发送到客户端
                    await websocket.send_bytes(frame_bytes)
                else:
                    # 如果没有帧可发送，发送空帧
                    empty_frame = np.zeros((1, 1, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', empty_frame)
                    frame_bytes = buffer.tobytes()
                    await websocket.send_bytes(frame_bytes)
            
            # 控制帧率
            await asyncio.sleep(0.05)  # ~20 FPS
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
            logger.error(f"ZED RGB WebSocket错误: {e}")
    finally:
        manager.disconnect(websocket)

@app.websocket("/ws/zed/depth")
async def zed_depth_endpoint(websocket: WebSocket):
    """ZED 深度图WebSocket端点"""
    # 尝试连接，如果达到限制则会返回False
    if not await manager.connect(websocket):
        return  # 连接被拒绝，直接返回
        
    try:
        # 添加超时机制，防止无限循环
        max_inactive_time = 60  # 最大不活跃时间（秒）
        start_time = time.time()
        
        while not shutdown_event.is_set():  # 检查关闭事件
            # 检查连接是否已超时
            if time.time() - start_time > max_inactive_time:
                logger.info(f"ZED Depth WebSocket连接超时，已断开")
                break
                
            with zed_server.depth_frame_lock:
                if zed_server.depth_frame is not None:
                    # 重置超时计时器
                    start_time = time.time()
                    
                    # 缩放图像以减少带宽
                    resized_frame = cv2.resize(zed_server.depth_frame, (640, 360))
                    # 编码为JPEG
                    _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                    
                    # 发送到客户端
                    await websocket.send_bytes(frame_bytes)
                else:
                    # 如果没有帧可发送，发送空帧
                    empty_frame = np.zeros((1, 1, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', empty_frame)
                    frame_bytes = buffer.tobytes()
                    await websocket.send_bytes(frame_bytes)
            
            # 控制帧率
            await asyncio.sleep(0.05)  # ~20 FPS
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if not shutdown_event.is_set():  # 只在非关闭状态下记录错误
            logger.error(f"ZED Depth WebSocket错误: {e}")
    finally:
        manager.disconnect(websocket)

# 修改清理资源函数，添加关闭WebSocket连接
async def async_cleanup_resources():
    """异步清理资源函数"""
    logger.info("正在异步清理资源...")
    await manager.close_all_connections()
    logger.info("异步资源清理完成")

def cleanup_resources():
    """同步清理资源函数，在程序退出时调用"""
    logger.info("正在清理主应用资源...")
    # 设置关闭事件，通知所有线程退出
    shutdown_event.set()
    
    # 创建一个新的事件循环来运行异步清理
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_cleanup_resources())
        loop.close()
    except Exception as e:
        logger.error(f"异步清理资源时出错: {e}")
    
    # 给线程一些时间来退出
    time.sleep(0.5)
    logger.info("主应用资源清理完成")

# 信号处理函数
def signal_handler(sig, frame):
    logger.info(f"主应用收到信号 {sig}，正在优雅关闭...")
    shutdown_event.set()

# 注册信号处理和退出处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup_resources)

# 添加ESP32控制API路由
@app.get("/api/esp32/status")
async def get_esp32_status():
    """获取所有ESP32控制板的状态"""
    return esp32_controller.get_all_status()

@app.get("/api/esp32/{board_id}")
async def get_esp32_board_status(board_id: str):
    """获取指定ESP32控制板的状态"""
    result = esp32_controller.get_board_status(board_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/api/esp32/{board_id}/button/{button_id}")
async def send_esp32_command(board_id: str, button_id: int):
    """发送命令到ESP32控制板"""
    result = await esp32_controller.send_command(board_id, button_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/debug/buttons")
async def get_debug_buttons():
    """调试端点：返回ESP32控制器的按钮配置"""
    return {
        "board1": esp32_controller.boards["board1"]["buttons"],
        "board2": esp32_controller.boards["board2"]["buttons"]
    }

@app.get("/api/lift/status")
async def get_lift_status():
    """获取登高车状态"""
    return lift_car_controller.get_info()

@app.post("/api/lift/button/{button_id}")
async def send_lift_command(button_id: int):
    """发送命令到登高车控制系统"""
    result = await lift_car_controller.send_command(button_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result 