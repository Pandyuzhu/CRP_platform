<template>
  <div class="arm-monitor-page">
    <div class="page-content">
      <div class="main-title">
        机械臂监控
        <div class="title-controls">
          <v-btn
            size="small"
            :color="debugMode ? 'primary' : 'secondary'"
            variant="tonal"
            class="debug-btn"
            @click="toggleDebugMode"
          >
            <v-icon size="small" class="mr-1">mdi-bug</v-icon>
            调试模式
          </v-btn>
        </div>
      </div>
      
      <div class="video-section">
        <WebRtcStream 
          @stream-status-change="updateStreamStatus" 
          :debugMode="debugMode"
          :streamUrl="webrtcUrl"
          :audioEnabled="true"
          ref="webrtcStream" 
        />
      </div>
      
      <div class="info-section">
        <div class="info-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-information-outline</v-icon>
            系统信息
          </div>
          <div class="info-content">
            <div class="info-item">
              <span class="info-label">后端API服务:</span>
              <span class="info-value" :class="{ 'online': isBackendConnected, 'offline': !isBackendConnected }">
                {{ isBackendConnected ? '在线' : '离线' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">机械臂摄像头:</span>
              <span class="info-value" :class="{ 'online': isArmCameraConnected, 'offline': !isArmCameraConnected }">
                {{ isArmCameraConnected ? '已连接' : '未连接' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">视频流状态:</span>
              <span class="info-value" :class="{ 'online': isStreamActive, 'offline': !isStreamActive }">
                {{ isStreamActive ? '活跃' : '非活跃' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">流地址:</span>
              <span class="info-value">{{ webrtcUrl.substring(0, 50) }}...</span>
            </div>
            <div class="info-item">
              <span class="info-label">协议类型:</span>
              <span class="info-value">WebRTC (Web Real-Time Communication)</span>
            </div>
            <div class="info-item">
              <span class="info-label">音频支持:</span>
              <span class="info-value">{{ isStreamActive ? '已启用' : '无数据' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">延迟优化:</span>
              <span class="info-value">{{ isStreamActive ? '已启用' : '无数据' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import WebRtcStream from '../components/video/WebRtcStream.vue';

export default {
  name: 'ArmMonitor',
  components: {
    WebRtcStream
  },
  data() {
    return {
      isStreamActive: false,
      isBackendConnected: false,
      isArmCameraConnected: false,
      checkBackendTimer: null,
      webrtcUrl: 'http://192.168.43.9/player/webrtc?streamPath=hlsram/live0&isMute=1&auto=1&aspect=0&hasAudio=1&username=admin&auth=f6fdffe48c908deb0f4c3bd36c032e72',
      debugMode: false
    }
  },
  methods: {
    updateStreamStatus(status) {
      this.isStreamActive = status;
      // 当视频流状态改变时，同时更新摄像头连接状态
      this.isArmCameraConnected = status;
    },
    checkBackendConnection() {
      // 检查后端API服务是否可用（使用机械臂专用API）
      fetch('/api/arm/status')
        .then(response => {
          if (response.ok) {
            this.isBackendConnected = true;
            return response.json();
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
        })
        .then(data => {
          console.log('Backend API status:', data);
        })
        .catch(error => {
          console.error('Backend API connection error:', error);
          this.isBackendConnected = false;
          
          // 如果机械臂API不可用，尝试检查基础API服务
          fetch('/api/')
            .then(response => {
              if (response.ok) {
                this.isBackendConnected = true;
                console.log('Backend base API is available');
              }
            })
            .catch(baseError => {
              console.error('Backend base API also failed:', baseError);
              this.isBackendConnected = false;
            });
        });
    },
    checkArmCameraStatus() {
      // 检查机械臂摄像头状态
      fetch('/api/arm/status')
        .then(response => {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
        })
        .then(data => {
          console.log('Arm camera status:', data);
          if (data && typeof data.camera_connected !== 'undefined') {
            this.isArmCameraConnected = data.camera_connected;
          } else {
            // 如果API返回的数据不包含camera_connected字段，根据视频流状态判断
            this.isArmCameraConnected = this.isStreamActive;
          }
        })
        .catch(error => {
          console.error('Arm camera status check error:', error);
          // 如果API不可用，根据视频流状态判断
          this.isArmCameraConnected = this.isStreamActive;
        });
    },
    toggleDebugMode() {
      this.debugMode = !this.debugMode;
      console.log('调试模式:', this.debugMode ? '开启' : '关闭');
    }
  },
  created() {
    console.log('ArmMonitor component created');
  },
  mounted() {
    console.log('ArmMonitor component mounted');
    // 初始检查
    this.checkBackendConnection();
    this.checkArmCameraStatus();
    
    // 定期检查后端连接
    this.checkBackendTimer = setInterval(() => {
      this.checkBackendConnection();
      this.checkArmCameraStatus();
    }, 5000); // 每5秒检查一次
  },
  beforeUnmount() {
    console.log('ArmMonitor component unmounting, cleaning up');
    // 清除定时器
    if (this.checkBackendTimer) {
      clearInterval(this.checkBackendTimer);
      this.checkBackendTimer = null;
    }
  }
}
</script>

<style scoped>
.arm-monitor-page {
  padding: 80px 20px 20px 20px;
  min-height: 100vh;
  background: #000;
  display: flex;
  flex-direction: column;
}

.page-content {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.main-title {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 28px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 30px;
  letter-spacing: 1px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-controls {
  display: flex;
  gap: 10px;
}

.debug-btn {
  min-width: 90px;
  font-size: 12px;
}

.video-section {
  width: 100%;
  height: 70vh;
  margin-bottom: 20px;
  border-radius: 10px;
  overflow: hidden;
}

.info-section {
  display: flex;
  gap: 20px;
}

.info-card {
  flex: 1;
  background: rgba(18, 18, 18, 0.7);
  border-radius: 10px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.info-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.info-value {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  word-break: break-all;
}

.info-value.online {
  color: #4cd964;
}

.info-value.offline {
  color: #ff3b30;
}

@media (max-width: 768px) {
  .video-section {
    height: 50vh;
  }
  
  .info-content {
    grid-template-columns: 1fr;
  }
}
</style> 