<template>
  <div class="zed-stream">
    <!-- 视频显示区域 -->
    <div class="video-container">
      <!-- RGB流 -->
      <div v-show="currentMode === 'rgb'" class="stream-wrapper">
        <img ref="rgbElement" class="video-feed" alt="RGB Stream" />
        <div v-if="!isZedConnected" class="offline-overlay">
          <div class="offline-message">RGB 视频信号离线</div>
        </div>
        <div v-if="isRgbConnecting" class="connecting-overlay">
          <div class="loader"></div>
        </div>
      </div>
      
      <!-- 深度图流 -->
      <div v-show="currentMode === 'depth'" class="stream-wrapper">
        <img ref="depthElement" class="video-feed" alt="Depth Stream" />
        <div v-if="!isZedConnected" class="offline-overlay">
          <div class="offline-message">深度图信号离线</div>
        </div>
        <div v-if="isDepthConnecting" class="connecting-overlay">
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
  </div>
</template>

<script>
export default {
  name: 'ZedStream',
  emits: ['stream-status-change'],
  data() {
    return {
      currentMode: 'rgb', // 'rgb' 或 'depth'
      isRgbActive: false,
      isDepthActive: false,
      isRgbConnecting: false,
      isDepthConnecting: false,
      rgbWebsocket: null,
      depthWebsocket: null,
      reconnectAttempts: {
        rgb: 0,
        depth: 0
      },
      maxReconnectAttempts: 5,
      reconnectTimers: {
        rgb: null,
        depth: null
      },
      deviceCheckTimer: null,
      consecutiveEmptyFrames: {
        rgb: 0,
        depth: 0
      },
      lastStatusCheckTime: 0,
      isZedConnected: false, // 新增ZED相机连接状态标志
      _hasInitialized: false
    }
  },
  computed: {
    isCurrentModeActive() {
      // 设备状态判断逻辑修改：优先考虑ZED相机是否物理连接
      if (this.isZedConnected) {
        return this.currentMode === 'rgb' ? this.isRgbActive : this.isDepthActive;
      }
      return false;
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
        this.isRgbActive = false;
        this.isDepthActive = false;
      }
      // 通知父组件ZED相机状态变化
      this.$emit('stream-status-change', this.isCurrentModeActive);
    }
  },
  methods: {
    switchMode(mode) {
      if (this.currentMode !== mode) {
        this.currentMode = mode;
        
        // 确保两种流都是连接的
        if (mode === 'rgb' && !this.isRgbActive && !this.rgbWebsocket && !this.isRgbConnecting) {
          console.log('切换到RGB模式，确保RGB流连接');
          this.startRgbStream();
        } else if (mode === 'depth' && !this.isDepthActive && !this.depthWebsocket && !this.isDepthConnecting) {
          console.log('切换到深度模式，确保深度流连接');
          this.startDepthStream();
        }
        
        console.log(`切换到${mode}模式`);
      }
    },
    
    // 确保在组件失活时停止所有WebSocket连接
    deactivateComponent() {
      console.log('ZedStream组件被缓存，停止所有连接');
      this.stopAllStreams();
    },
    
    // 组件重新激活时
    activateComponent() {
      console.log('ZedStream组件被激活，重新检查连接状态');
      // 先检查状态，再决定是否需要重新连接
      this.checkZedConnectionStatus();
    },
    
    checkDeviceStatus() {
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
          
          // 检查后端日志中是否有ZED相机连接的信息
          if (data && typeof data.zed_connected !== 'undefined') {
            // 明确更新ZED相机连接状态
            this.isZedConnected = data.zed_connected;
            
            // 如果后端明确指示ZED相机已连接但是当前显示为离线，强制更新状态
            if (data.zed_connected === true) {
              console.log('Backend reports ZED camera is connected, updating UI');
            } else if (data.zed_connected === false) {
              // 如果后端明确指示ZED相机已断开，强制更新状态
              console.log('Backend reports ZED camera is disconnected, updating UI');
              this.isRgbActive = false;
              this.isDepthActive = false;
            }
          } else {
            // 如果API没有直接提供ZED相机连接状态，根据是否能接收到视频帧来推断
            // 如果有活跃的RGB或深度流，认为ZED相机是连接的
            if (this.isRgbActive || this.isDepthActive) {
              this.isZedConnected = true;
            }
          }
        })
        .catch(error => {
          console.error('Failed to check ZED camera status:', error);
        });
    },
    
    startRgbStream() {
      // 防止重复连接
      if (this.isRgbConnecting || this.isRgbActive || this.rgbWebsocket) {
        console.log('RGB流已连接或正在连接中，不重复连接');
        return;
      }
      
      this.isRgbConnecting = true;
      this.consecutiveEmptyFrames.rgb = 0;
      
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:3000';
        const wsUrl = `${protocol}//${host}/ws/zed/rgb`;
        
        console.log(`连接到RGB WebSocket: ${wsUrl}`);
        this.rgbWebsocket = new WebSocket(wsUrl);
        
        this.rgbWebsocket.onopen = () => {
          console.log('RGB WebSocket连接已建立');
          this.isRgbConnecting = false;
          this.reconnectAttempts.rgb = 0;
          // WebSocket连接成功时检查ZED相机状态
          this.checkDeviceStatus();
        };
        
        this.rgbWebsocket.onmessage = (event) => {
          // 检查数据大小，如果是空图像（小于100字节），可能是设备发送的心跳包
          if (event.data.byteLength < 100) {
            console.log('Received small RGB frame, might be heartbeat');
            return;
          }
          
          // 收到有效的视频帧，说明ZED相机物理连接正常
          this.isZedConnected = true;
          
          // 只有当收到有效帧且大小正常时，才设置为活跃
          if (event.data.byteLength > 1000) {
            this.isRgbActive = true;
            this.consecutiveEmptyFrames.rgb = 0;
          }
          
          // 将接收到的二进制数据转换为图像
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          
          // 更新图像元素
          if (this.$refs.rgbElement) {
            this.$refs.rgbElement.src = url;
            
            // 图像加载后释放对象URL以避免内存泄漏
            this.$refs.rgbElement.onload = () => {
              URL.revokeObjectURL(url);
            };
          }
        };
        
        this.rgbWebsocket.onerror = (error) => {
          console.error('RGB WebSocket错误:', error);
          this.handleConnectionFailure('rgb');
        };
        
        this.rgbWebsocket.onclose = () => {
          console.log('RGB WebSocket连接关闭');
          this.isRgbActive = false;
          this.isRgbConnecting = false;
          this.rgbWebsocket = null;
          // WebSocket关闭后重新检查设备状态
          setTimeout(() => this.checkDeviceStatus(), 1000);
        };
      } catch (error) {
        console.error('设置RGB WebSocket时出错:', error);
        this.handleConnectionFailure('rgb');
      }
    },
    
    startDepthStream() {
      // 防止重复连接
      if (this.isDepthConnecting || this.isDepthActive || this.depthWebsocket) {
        console.log('Depth流已连接或正在连接中，不重复连接');
        return;
      }
      
      this.isDepthConnecting = true;
      this.consecutiveEmptyFrames.depth = 0;
      
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:3000';
        const wsUrl = `${protocol}//${host}/ws/zed/depth`;
        
        console.log(`连接到Depth WebSocket: ${wsUrl}`);
        this.depthWebsocket = new WebSocket(wsUrl);
        
        this.depthWebsocket.onopen = () => {
          console.log('Depth WebSocket连接已建立');
          this.isDepthConnecting = false;
          this.reconnectAttempts.depth = 0;
          // WebSocket连接成功时检查ZED相机状态
          this.checkDeviceStatus();
        };
        
        this.depthWebsocket.onmessage = (event) => {
          // 检查数据大小，如果是空图像（小于100字节），可能是设备发送的心跳包
          if (event.data.byteLength < 100) {
            console.log('Received small Depth frame, might be heartbeat');
            return;
          }
          
          // 收到有效的视频帧，说明ZED相机物理连接正常
          this.isZedConnected = true;
          
          // 只有当收到有效帧且大小正常时，才设置为活跃
          if (event.data.byteLength > 1000) {
            this.isDepthActive = true;
            this.consecutiveEmptyFrames.depth = 0;
          }
          
          // 将接收到的二进制数据转换为图像
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          
          // 更新图像元素
          if (this.$refs.depthElement) {
            this.$refs.depthElement.src = url;
            
            // 图像加载后释放对象URL以避免内存泄漏
            this.$refs.depthElement.onload = () => {
              URL.revokeObjectURL(url);
            };
          }
        };
        
        this.depthWebsocket.onerror = (error) => {
          console.error('Depth WebSocket错误:', error);
          this.handleConnectionFailure('depth');
        };
        
        this.depthWebsocket.onclose = () => {
          console.log('Depth WebSocket连接关闭');
          this.isDepthActive = false;
          this.isDepthConnecting = false;
          this.depthWebsocket = null;
          // WebSocket关闭后重新检查设备状态
          setTimeout(() => this.checkDeviceStatus(), 1000);
        };
      } catch (error) {
        console.error('设置Depth WebSocket时出错:', error);
        this.handleConnectionFailure('depth');
      }
    },
    
    stopStream(type) {
      console.log(`停止${type}流`);
      if (type === 'rgb' && this.rgbWebsocket) {
        console.log('关闭RGB WebSocket连接');
        this.rgbWebsocket.onclose = null; // 防止触发onclose事件处理器
        this.rgbWebsocket.close();
        this.rgbWebsocket = null;
        this.isRgbActive = false;
        this.isRgbConnecting = false;
        clearTimeout(this.reconnectTimers.rgb);
      } else if (type === 'depth' && this.depthWebsocket) {
        console.log('关闭Depth WebSocket连接');
        this.depthWebsocket.onclose = null; // 防止触发onclose事件处理器
        this.depthWebsocket.close();
        this.depthWebsocket = null;
        this.isDepthActive = false;
        this.isDepthConnecting = false;
        clearTimeout(this.reconnectTimers.depth);
      }
    },
    
    handleConnectionFailure(type) {
      if (type === 'rgb') {
        this.isRgbActive = false;
        this.isRgbConnecting = false;
        
        if (this.rgbWebsocket) {
          this.rgbWebsocket.close();
          this.rgbWebsocket = null;
        }
      } else if (type === 'depth') {
        this.isDepthActive = false;
        this.isDepthConnecting = false;
        
        if (this.depthWebsocket) {
          this.depthWebsocket.close();
          this.depthWebsocket = null;
        }
      }
      
      // 连接失败后延迟检查设备状态
      setTimeout(() => this.checkDeviceStatus(), 1000);
    },
    
    stopAllStreams() {
      console.log('停止所有ZED流');
      this.stopStream('rgb');
      this.stopStream('depth');
      
      if (this.deviceCheckTimer) {
        clearInterval(this.deviceCheckTimer);
        this.deviceCheckTimer = null;
      }
    },
    
    // 尝试直接从后端获取ZED相机连接状态
    checkZedConnectionStatus() {
      // 这里可以调用一个专门用于检查ZED相机连接状态的API
      // 如果后端没有提供这样的API，可以考虑添加一个
      fetch('/api/stream_status')
        .then(response => response.json())
        .then(data => {
          console.log('Checking ZED physical connection status:', data);
          // 当后端日志有"已连接ZED客户端"时，应该将isZedConnected设为true
          if (data && data.zed_connected === true) {
            this.isZedConnected = true;
            console.log('ZED camera is physically connected');
          } else if (data && data.zed_connected === false) {
            // 如果明确断开，更新状态
            this.isZedConnected = false;
            this.isRgbActive = false;
            this.isDepthActive = false;
            console.log('ZED camera is physically disconnected');
          }
        })
        .catch(error => {
          console.error('Failed to check ZED physical connection:', error);
        });
    }
  },
  created() {
    console.log('ZedStream component created');
  },
  mounted() {
    console.log('ZedStream component mounted');
    
    // 先检查ZED相机物理连接状态
    this.checkZedConnectionStatus();
    
    // 仅当组件首次挂载时自动连接，而不是每次切换时
    if (!this._hasInitialized) {
      // 自动连接默认的RGB流
      setTimeout(() => {
        this.startRgbStream();
      }, 500);
      
      // 始终连接深度流，无论当前模式如何
      setTimeout(() => {
        this.startDepthStream();
      }, 1000);
      
      this._hasInitialized = true;
    }
    
    // 定期检查设备状态
    this.deviceCheckTimer = setInterval(() => {
      this.checkDeviceStatus();
      
      // 如果已经收到有效视频帧但isZedConnected仍为false，强制更新
      if ((this.isRgbActive || this.isDepthActive) && !this.isZedConnected) {
        console.log('Video streams active but ZED connection state is false, updating');
        this.isZedConnected = true;
      }
      
      // 确保深度流始终处于连接状态
      if (!this.depthWebsocket && !this.isDepthConnecting) {
        console.log('Depth stream not connected, attempting to connect');
        this.startDepthStream();
      }
    }, 2000); // 每2秒检查一次，更频繁些以确保状态一致
  },
  beforeUnmount() {
    console.log('ZedStream component unmounting, cleaning up');
    this.stopAllStreams();
  },
  activated() {
    // 当使用keep-alive时，组件被激活时调用
    console.log('ZedStream component activated');
    this.activateComponent();
  },
  deactivated() {
    // 当使用keep-alive时，组件被缓存时调用
    console.log('ZedStream component deactivated');
    this.deactivateComponent();
  }
}
</script>

<style scoped>
.zed-stream {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #000;
  border-radius: 10px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
}

.video-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.stream-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.video-feed {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transform: scale(1.2);
}

.connecting-overlay, .offline-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.7);
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.offline-message {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
  letter-spacing: 1px;
}

.mode-toggle {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 20;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-btn {
  min-width: 100px;
}

.info-overlay {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  padding: 10px 15px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
  z-index: 20;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: rgba(255, 255, 255, 0.7);
}

.info-value {
  color: rgba(255, 0, 0, 0.7);
  font-weight: 500;
}

.info-value.online {
  color: rgba(0, 255, 0, 0.7);
}
</style> 