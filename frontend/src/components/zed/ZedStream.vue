<template>
  <div class="zed-stream">
    <!-- 视频显示区域 -->
    <div class="video-container">
      <!-- 单一图像容器，通过CSS切换显示 -->
      <div class="stream-wrapper">
        <img ref="streamElement" class="video-feed" alt="ZED Stream" />
        <div v-if="!isZedConnected" class="offline-overlay">
          <div class="offline-message">ZED 相机离线</div>
        </div>
        <div v-if="isConnecting" class="connecting-overlay">
          <div class="loader"></div>
        </div>
      </div>
      
      <!-- 流模式切换按钮 -->
      <div class="mode-toggle">
        <v-btn
          :color="currentMode === 'rgb' ? 'primary' : 'secondary'"
          variant="tonal"
          class="toggle-btn"
          @click="switchMode('rgb')"
          :disabled="currentMode === 'rgb'"
        >
          <v-icon class="mr-1">mdi-camera</v-icon>
          RGB
        </v-btn>
        <v-btn
          :color="currentMode === 'depth' ? 'primary' : 'secondary'"
          variant="tonal"
          class="toggle-btn"
          @click="switchMode('depth')"
          :disabled="currentMode === 'depth'"
        >
          <v-icon class="mr-1">mdi-chart-bubble</v-icon>
          深度图
        </v-btn>
      </div>
    </div>
    
    <!-- 信息叠加层 -->
    <div class="info-overlay">
      <div class="info-item">
        <span class="info-label">状态:</span>
        <span class="info-value" :class="{ 'online': isZedConnected }">
          {{ isZedConnected ? '在线' : '离线' }}
        </span>
      </div>
      <div class="info-item">
        <span class="info-label">当前模式:</span>
        <span class="info-value">{{ currentMode === 'rgb' ? 'RGB 视图' : '深度图' }}</span>
      </div>
    </div>

    <!-- 调试信息，开发时使用 -->
    <div v-if="false" class="debug-overlay">
      <pre>{{ debugInfo }}</pre>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ZedStream',
  emits: ['stream-status-change'],
  data() {
    return {
      currentMode: 'rgb', // 'rgb' 或 'depth'
      isStreamActive: false,
      isConnecting: false,
      websocket: null,
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimer: null,
      deviceCheckTimer: null,
      consecutiveEmptyFrames: 0,
      lastStatusCheckTime: 0,
      isZedConnected: false, // ZED相机连接状态标志
      _hasInitialized: false,
      lastReceivedMode: null, // 跟踪从服务器接收的最后一个模式
      debugInfo: { serverMode: null, lastFrameTime: null }
    }
  },
  computed: {
    isCurrentModeActive() {
      // 设备状态判断逻辑：优先考虑ZED相机是否物理连接
      return this.isZedConnected && this.isStreamActive;
    }
  },
  watch: {
    isCurrentModeActive(newValue) {
      this.$emit('stream-status-change', newValue);
    },
    // 监听ZED相机连接状态
    isZedConnected(newValue) {
      console.log('ZED camera physical connection status changed:', newValue);
      // 当ZED相机断开连接时，确保其他状态也随之更新
      if (!newValue) {
        this.isStreamActive = false;
      }
      // 通知父组件ZED相机状态变化
      this.$emit('stream-status-change', this.isCurrentModeActive);
    }
  },
  methods: {
    switchMode(mode) {
      if (this.currentMode !== mode) {
        console.log(`请求切换到${mode}模式`);
        this.currentMode = mode;
        
        // 如果WebSocket已连接，发送模式切换命令
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          const modeMessage = JSON.stringify({ mode: mode });
          console.log(`发送模式切换命令: ${modeMessage}`);
          this.websocket.send(modeMessage);
        }
      }
    },
    
    // 确保在组件失活时停止WebSocket连接
    deactivateComponent() {
      console.log('ZedStream组件被缓存，停止连接');
      this.stopStream();
    },
    
    // 组件重新激活时
    activateComponent() {
      console.log('ZedStream组件被激活，重新检查连接状态');
      // 先检查状态，再决定是否需要重新连接
      this.checkZedConnectionStatus();
    },
    
    checkZedConnectionStatus() {
      // 防止过于频繁地检查
      const now = Date.now();
      if (now - this.lastStatusCheckTime < 2000) {
        return;
      }
      this.lastStatusCheckTime = now;
      
      // 通过API检查ZED相机状态
      fetch('/api/stream_status')
        .then(response => response.json())
        .then(data => {
          console.log('ZED camera status checked:', data);
          
          // 检查后端是否有ZED相机连接的信息
          if (data && typeof data.zed_connected !== 'undefined') {
            // 明确更新ZED相机连接状态
            this.isZedConnected = data.zed_connected;
            
            // 如果后端明确指示ZED相机已连接但是当前显示为离线，强制更新状态
            if (data.zed_connected === true && !this.isStreamActive && !this.websocket) {
              console.log('Backend reports ZED camera is connected, starting stream');
              this.startStream();
            } else if (data.zed_connected === false) {
              // 如果后端明确指示ZED相机已断开，强制更新状态
              console.log('Backend reports ZED camera is disconnected, updating UI');
              this.isStreamActive = false;
              this.stopStream();
            }
          }
        })
        .catch(error => {
          console.error('Failed to check ZED camera status:', error);
        });
    },
    
    startStream() {
      // 防止重复连接
      if (this.isConnecting || this.isStreamActive || this.websocket) {
        console.log('ZED流已连接或正在连接中，不重复连接');
        return;
      }
      
      this.isConnecting = true;
      this.consecutiveEmptyFrames = 0;
      
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:3000';
        const wsUrl = `${protocol}//${host}/ws/zed`;
        
        console.log(`连接到ZED WebSocket: ${wsUrl}`);
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
          console.log('ZED WebSocket连接已建立');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          
          // 发送当前模式
          const modeMessage = JSON.stringify({ mode: this.currentMode });
          console.log(`连接后发送初始模式: ${modeMessage}`);
          this.websocket.send(modeMessage);
          
          // WebSocket连接成功时检查ZED相机状态
          this.checkZedConnectionStatus();
        };
        
        this.websocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            // 更新调试信息
            this.debugInfo.serverMode = message.mode;
            this.debugInfo.lastFrameTime = new Date().toISOString();
            
            // 处理状态信息
            if (message.zed_connected !== undefined) {
              this.isZedConnected = message.zed_connected;
            }
            
            // 记录服务器返回的模式
            if (message.mode !== undefined) {
              this.lastReceivedMode = message.mode;
            }
            
            // 如果有帧数据，显示图像
            if (message.frame_data) {
              // 收到有效的视频帧，说明ZED相机物理连接正常
              this.isStreamActive = true;
              this.consecutiveEmptyFrames = 0;
              
              // 显示图像
              if (this.$refs.streamElement) {
                this.$refs.streamElement.src = `data:image/jpeg;base64,${message.frame_data}`;
              }
            } else {
              // 没有帧数据，可能是相机离线
              this.consecutiveEmptyFrames++;
              if (this.consecutiveEmptyFrames > 10) {
                this.isStreamActive = false;
              }
            }
          } catch (error) {
            console.error('Error processing WebSocket message:', error);
          }
        };
        
        this.websocket.onclose = (event) => {
          console.log(`ZED WebSocket连接已关闭: ${event.code} ${event.reason}`);
          this.cleanupWebSocket();
          
          // 如果不是用户主动关闭，并且重连尝试次数未超过最大值，尝试重连
          if (!this._isUserClosing && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };
        
        this.websocket.onerror = (error) => {
          console.error('ZED WebSocket错误:', error);
          this.cleanupWebSocket();
          
          // 如果重连尝试次数未超过最大值，尝试重连
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        console.error('创建WebSocket连接时出错:', error);
        this.isConnecting = false;
        
        // 如果重连尝试次数未超过最大值，尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      }
    },
    
    stopStream() {
      this._isUserClosing = true;
      this.cleanupWebSocket();
      
      // 清除重连定时器
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      
      this.isStreamActive = false;
    },
    
    cleanupWebSocket() {
      if (this.websocket) {
        // 如果WebSocket仍处于连接或正在连接状态，关闭它
        if (this.websocket.readyState === WebSocket.OPEN || 
            this.websocket.readyState === WebSocket.CONNECTING) {
          this.websocket.close();
        }
        this.websocket = null;
      }
      this.isConnecting = false;
    },
    
    scheduleReconnect() {
      this.reconnectAttempts++;
      const delay = Math.min(30000, Math.pow(2, this.reconnectAttempts) * 1000);
      console.log(`计划 ${delay}ms 后尝试第 ${this.reconnectAttempts} 次重连ZED WebSocket`);
      
      this.reconnectTimer = setTimeout(() => {
        console.log(`正在尝试第 ${this.reconnectAttempts} 次重连ZED WebSocket`);
        this.startStream();
      }, delay);
    }
  },
  mounted() {
    console.log('ZedStream组件已挂载');
    this._hasInitialized = true;
    
    // 启动设备状态检查定时器
    this.deviceCheckTimer = setInterval(() => {
      this.checkZedConnectionStatus();
    }, 5000);
    
    // 初次检查设备状态
    this.checkZedConnectionStatus();
    
    // 初始启动流
    this.startStream();
  },
  beforeDestroy() {
    console.log('ZedStream组件即将销毁');
    
    // 清理所有资源
    this.stopStream();
    
    if (this.deviceCheckTimer) {
      clearInterval(this.deviceCheckTimer);
      this.deviceCheckTimer = null;
    }
  }
}
</script>

<style scoped>
.zed-stream {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 8px;
  background-color: #1a1a1a;
}

.video-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.stream-wrapper {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.video-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.offline-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.offline-message {
  color: #ff3b30;
  font-size: 18px;
  font-weight: 500;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.6);
  padding: 15px 25px;
  border-radius: 8px;
  border: 1px solid rgba(255, 59, 48, 0.3);
}

.connecting-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 5;
}

.loader {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid #ffffff;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.mode-toggle {
  position: absolute;
  bottom: 15px;
  right: 15px;
  display: flex;
  gap: 8px;
  z-index: 20;
}

.toggle-btn {
  padding: 0 15px;
  height: 36px;
  border-radius: 18px;
  font-size: 12px;
  text-transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.info-overlay {
  position: absolute;
  top: 15px;
  left: 15px;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 10px;
  border-radius: 8px;
  z-index: 15;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.info-value {
  color: #ff3b30;
  font-size: 12px;
  font-weight: 500;
}

.info-value.online {
  color: #4cd964;
}

.debug-overlay {
  position: absolute;
  bottom: 15px;
  left: 15px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px;
  border-radius: 8px;
  z-index: 15;
  font-size: 12px;
  max-width: 400px;
  overflow: auto;
}
</style> 