<template>
  <div class="video-stream">
    <!-- WebSocket Video Stream -->
    <img v-if="isStreamActive" ref="videoElement" class="video-feed" alt="Video Stream" />
    
    <!-- Loading State -->
    <div v-if="isConnecting" class="connecting-overlay">
      <div class="loader"></div>
    </div>
    
    <!-- Offline State -->
    <div v-if="!isStreamActive && !isConnecting" class="offline-overlay">
      <div class="offline-message">VIDEO SIGNAL OFFLINE</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoStream',
  emits: ['stream-status-change'],
  props: {
    autoConnect: {
      type: Boolean,
      default: true
    },
    wsEndpoint: {
      type: String,
      default: 'ws/video'
    }
  },
  data() {
    return {
      isStreamActive: false,
      isConnecting: false,
      websocket: null,
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimer: null,
      deviceCheckTimer: null,
      consecutiveEmptyFrames: 0,
      lastStatusCheckTime: 0,
      _hasInitialized: false
    }
  },
  watch: {
    isStreamActive(newValue) {
      this.$emit('stream-status-change', newValue);
    }
  },
  methods: {
    startStream() {
      // 防止重复连接
      if (this.isConnecting || this.isStreamActive || this.websocket) {
        console.log('视频流已连接或正在连接中，不重复连接');
        return;
      }
      
      this.isConnecting = true;
      this.consecutiveEmptyFrames = 0;
      
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:3000';
        const wsUrl = `${protocol}//${host}/${this.wsEndpoint}`;
        
        console.log(`Connecting to WebSocket: ${wsUrl}`);
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
          console.log('WebSocket connection established');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          
          // 立即检查设备状态，但不自动将其设为活跃
          this.checkDeviceStatus();
        };
        
        this.websocket.onmessage = (event) => {
          // 检查数据大小，如果是空图像（小于100字节），则认为是离线状态
          if (event.data.byteLength < 100) {
            console.log('Received empty image, device is offline');
            // 立即将设备状态设为离线，不需要等待多次确认
            this.isStreamActive = false;
            return;
          }
          
          // 只有当收到有效帧且大小正常时，才设置为活跃
          // 检查图像是否是一个有效的帧（通常视频帧会比较大）
          if (event.data.byteLength > 1000) {
            this.isStreamActive = true;
            this.consecutiveEmptyFrames = 0;
          }
          
          // Convert received binary data to an image
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          
          // Update the image element
          if (this.$refs.videoElement) {
            this.$refs.videoElement.src = url;
            
            // Release the object URL after the image loads to avoid memory leaks
            this.$refs.videoElement.onload = () => {
              URL.revokeObjectURL(url);
            };
          }
        };
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.handleConnectionFailure();
        };
        
        this.websocket.onclose = () => {
          console.log('WebSocket connection closed');
          if (this.isStreamActive) {
            this.isStreamActive = false;
          }
          
          this.isConnecting = false;
          this.websocket = null;
          
          // 连接关闭后立即重新检查设备状态
          this.checkDeviceStatus();
        };
      } catch (error) {
        console.error('Error setting up WebSocket:', error);
        this.handleConnectionFailure();
      }
    },
    
    checkDeviceStatus() {
      // 防止过于频繁地检查
      const now = Date.now();
      if (now - this.lastStatusCheckTime < 2000) {
        return;
      }
      this.lastStatusCheckTime = now;
      
      // 通过API检查设备状态
      fetch('/api/stream_status')
        .then(response => response.json())
        .then(data => {
          console.log('Device status from API:', data);
          // 明确检查设备是否真的在线 (is_streaming)
          if (!data.is_streaming) {
            this.isStreamActive = false;
          }
        })
        .catch(error => {
          console.error('Failed to check device status:', error);
          this.isStreamActive = false;
        });
    },
    
    stopStream() {
      console.log('停止视频流');
      if (this.websocket) {
        console.log('关闭WebSocket连接');
        this.websocket.onclose = null; // 防止触发onclose事件处理器
        this.websocket.close();
        this.websocket = null;
      }
      this.isStreamActive = false;
      this.isConnecting = false;
      clearTimeout(this.reconnectTimer);
      clearInterval(this.deviceCheckTimer);
    },
    
    handleConnectionFailure() {
      this.isStreamActive = false;
      this.isConnecting = false;
      
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }
    },
    
    attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = setTimeout(() => {
          this.startStream();
        }, 2000);
      } else {
        console.log('Maximum reconnect attempts reached, showing offline state');
        this.isStreamActive = false;
        this.isConnecting = false;
      }
    },
    
    // 确保在组件失活时停止WebSocket连接
    deactivateComponent() {
      console.log('VideoStream组件被缓存，停止连接');
      this.stopStream();
    },
    
    // 组件重新激活时
    activateComponent() {
      console.log('VideoStream组件被激活，重新检查连接状态');
      // 只有在autoConnect时才自动重连
      if (this.autoConnect) {
        this.startStream();
      }
    }
  },
  mounted() {
    // Start stream after a brief delay if autoConnect is true
    if (this.autoConnect && !this._hasInitialized) {
      setTimeout(() => {
        this.startStream();
      }, 500);
      
      this._hasInitialized = true;
    }
    
    // 定期检查设备状态，但频率降低，避免频繁切换状态
    this.deviceCheckTimer = setInterval(() => {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.checkDeviceStatus();
      }
    }, 10000); // 每10秒检查一次，降低频率
  },
  beforeUnmount() {
    console.log('VideoStream component unmounting, cleaning up');
    this.stopStream();
  },
  activated() {
    // 当使用keep-alive时，组件被激活时调用
    console.log('VideoStream component activated');
    this.activateComponent();
  },
  deactivated() {
    // 当使用keep-alive时，组件被缓存时调用
    console.log('VideoStream component deactivated');
    this.deactivateComponent();
  }
}
</script>

<style scoped>
.video-stream {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: #000;
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
  background: #000;
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.offline-message {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  color: rgba(255,255,255,0.7);
  font-size: 16px;
  letter-spacing: 1px;
}
</style> 