<template>
  <div class="spray-monitor-page">
    <div class="page-content">
      <div class="main-title">
        UHPC 喷射监控
        <div class="view-mode-controls">
          <v-btn
            size="small"
            :color="currentMode === 'rgb' ? 'primary' : 'secondary'"
            variant="tonal"
            class="mode-btn"
            @click="switchMode('rgb')"
          >
            <v-icon size="small" class="mr-1">mdi-camera</v-icon>
            RGB视图
          </v-btn>
          <v-btn
            size="small"
            :color="currentMode === 'depth' ? 'primary' : 'secondary'"
            variant="tonal"
            class="mode-btn"
            @click="switchMode('depth')"
          >
            <v-icon size="small" class="mr-1">mdi-chart-bubble</v-icon>
            深度图
          </v-btn>
        </div>
      </div>
      
      <div class="video-section">
        <ZedStream @stream-status-change="updateStreamStatus" ref="zedStream" />
      </div>
      
      <div class="info-section">
        <div class="info-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-information-outline</v-icon>
            系统信息
          </div>
          <div class="info-content">
            <div class="info-item">
              <span class="info-label">后端连接:</span>
              <span class="info-value" :class="{ 'online': isBackendConnected, 'offline': !isBackendConnected }">
                {{ isBackendConnected ? '在线' : '离线' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">ZED 相机:</span>
              <span class="info-value" :class="{ 'online': isZedConnected, 'offline': !isZedConnected }">
                {{ isZedConnected ? '已连接' : '未连接' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">当前视图:</span>
              <span class="info-value">{{ currentMode === 'rgb' ? 'RGB视图' : '深度图' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">分辨率:</span>
              <span class="info-value">{{ isZedConnected ? '1280x720' : '无数据' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">深度检测范围:</span>
              <span class="info-value">{{ isZedConnected ? '800mm - 1200mm' : '无数据' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ZedStream from '../components/zed/ZedStream.vue';

export default {
  name: 'SprayMonitor',
  components: {
    ZedStream
  },
  data() {
    return {
      isStreamActive: false,
      isBackendConnected: false,
      isZedConnected: false,
      checkBackendTimer: null,
      currentMode: 'rgb' // 默认为RGB模式
    }
  },
  methods: {
    updateStreamStatus(status) {
      this.isStreamActive = status;
    },
    checkBackendConnection() {
      // 使用fetch API检测后端连接状态
      fetch('/api/stream_status')
        .then(response => {
          this.isBackendConnected = true;
          return response.json();
        })
        .then(data => {
          console.log('Backend status:', data);
          // 更新ZED相机连接状态
          if (data && typeof data.zed_connected !== 'undefined') {
            this.isZedConnected = data.zed_connected;
          }
        })
        .catch(error => {
          console.error('Backend connection error:', error);
          this.isBackendConnected = false;
          this.isZedConnected = false;
        });
    },
    // 切换视图模式
    switchMode(mode) {
      if (this.currentMode !== mode) {
        this.currentMode = mode;
        // 调用ZedStream组件的switchMode方法
        if (this.$refs.zedStream) {
          this.$refs.zedStream.switchMode(mode);
        }
      }
    }
  },
  created() {
    console.log('SprayMonitor component created');
  },
  mounted() {
    console.log('SprayMonitor component mounted');
    // 初始检查
    this.checkBackendConnection();
    
    // 定期检查后端连接
    this.checkBackendTimer = setInterval(() => {
      this.checkBackendConnection();
    }, 5000); // 每5秒检查一次
  },
  beforeUnmount() {
    console.log('SprayMonitor component unmounting, cleaning up');
    // 清除定时器
    if (this.checkBackendTimer) {
      clearInterval(this.checkBackendTimer);
      this.checkBackendTimer = null;
    }
  }
}
</script>

<style scoped>
.spray-monitor-page {
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

.view-mode-controls {
  display: flex;
  gap: 10px;
}

.mode-btn {
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