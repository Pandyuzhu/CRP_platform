<template>
  <div class="sprayer-monitor-page">
    <div class="page-content">
      <div class="main-title">
        喷射操作台
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
      
      <div class="main-layout">
        <div class="left-panel">
          <!-- 登高车控制区域 -->
          <div class="control-card">
            <div class="card-title">
              <v-icon color="primary" class="mr-2">mdi-crane</v-icon>
              登高车控制
              <div class="status-indicator active">
                可用
              </div>
            </div>
            <div class="control-buttons">
              <!-- 关节1控制 -->
              <div class="joint-control">
                <div class="joint-title">关节1控制</div>
                <div class="control-row">
                  <v-btn
                    v-for="button in getJointButtons('joint1')"
                    :key="button.id"
                    :color="getButtonColor(button)"
                    :variant="button.status ? 'flat' : 'outlined'"
                    class="control-btn"
                    @click="sendLiftCommand(button.id)"
                  >
                    <v-icon class="mr-2">{{ getButtonIcon(button) }}</v-icon>
                    {{ button.name }}
                  </v-btn>
                </div>
              </div>
              
              <!-- 关节2控制 -->
              <div class="joint-control">
                <div class="joint-title">关节2控制</div>
                <div class="control-row">
                  <v-btn
                    v-for="button in getJointButtons('joint2')"
                    :key="button.id"
                    :color="getButtonColor(button)"
                    :variant="button.status ? 'flat' : 'outlined'"
                    class="control-btn"
                    @click="sendLiftCommand(button.id)"
                  >
                    <v-icon class="mr-2">{{ getButtonIcon(button) }}</v-icon>
                    {{ button.name }}
                  </v-btn>
                </div>
              </div>
              
              <!-- 关节3控制 -->
              <div class="joint-control">
                <div class="joint-title">关节3控制</div>
                <div class="control-row">
                  <v-btn
                    v-for="button in getJointButtons('joint3')"
                    :key="button.id"
                    :color="getButtonColor(button)"
                    :variant="button.status ? 'flat' : 'outlined'"
                    class="control-btn"
                    @click="sendLiftCommand(button.id)"
                  >
                    <v-icon class="mr-2">{{ getButtonIcon(button) }}</v-icon>
                    {{ button.name }}
                  </v-btn>
                </div>
              </div>
              
              <!-- 全部停止按钮 -->
              <div class="control-row mt-4">
                <v-btn
                  color="error"
                  variant="flat"
                  class="control-btn"
                  @click="sendLiftCommand(10)"
                  size="large"
                >
                  <v-icon class="mr-2">mdi-stop-circle</v-icon>
                  全部停止
                </v-btn>
              </div>
            </div>
          </div>
        </div>
        
        <div class="right-panel">
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
                <span class="info-label">登高车:</span>
                <span class="info-value online">
                  已连接
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 操作提示弹窗 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import ZedStream from '../components/zed/ZedStream.vue';

export default {
  name: 'SprayerMonitor',
  components: {
    ZedStream
  },
  data() {
    return {
      isStreamActive: false,
      isBackendConnected: false,
      isZedConnected: false,
      checkBackendTimer: null,
      currentMode: 'rgb', // 默认为RGB模式
      
      // 登高车按钮
      liftButtons: [],
      
      // 通知消息
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
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
    },
    
    loadLiftButtons() {
      // 加载登高车按钮数据
      fetch('/api/lift/status')
        .then(response => {
          if (!response.ok) {
            throw new Error('登高车数据获取失败');
          }
          return response.json();
        })
        .then(data => {
          console.log('Lift car data:', data);
          
          // 更新按钮数据
          if (data.buttons) {
            this.liftButtons = data.buttons;
          }
        })
        .catch(error => {
          console.error('Lift car data error:', error);
          // 初始化默认按钮
          this.initDefaultLiftButtons();
        });
    },
    
    // 获取特定关节的按钮
    getJointButtons(jointName) {
      return this.liftButtons.filter(btn => btn.joint === jointName);
    },
    
    // 获取按钮颜色
    getButtonColor(button) {
      if (button.action === '伸展') return 'success';
      if (button.action === '屈曲') return 'warning';
      return 'error'; // 停止按钮
    },
    
    // 获取按钮图标
    getButtonIcon(button) {
      if (button.action === '伸展') return 'mdi-arrow-up';
      if (button.action === '屈曲') return 'mdi-arrow-down';
      return 'mdi-stop'; // 停止按钮
    },
    
    // 初始化默认登高车按钮
    initDefaultLiftButtons() {
      this.liftButtons = [
        {"id": 1, "name": "关节1伸展", "action": "伸展", "joint": "joint1", "value": 1, "status": false},
        {"id": 2, "name": "关节1停止", "action": "停止", "joint": "joint1", "value": 0, "status": false},
        {"id": 3, "name": "关节1屈曲", "action": "屈曲", "joint": "joint1", "value": 2, "status": false},
        
        {"id": 4, "name": "关节2伸展", "action": "伸展", "joint": "joint2", "value": 1, "status": false},
        {"id": 5, "name": "关节2停止", "action": "停止", "joint": "joint2", "value": 0, "status": false},
        {"id": 6, "name": "关节2屈曲", "action": "屈曲", "joint": "joint2", "value": 2, "status": false},
        
        {"id": 7, "name": "关节3伸展", "action": "伸展", "joint": "joint3", "value": 1, "status": false},
        {"id": 8, "name": "关节3停止", "action": "停止", "joint": "joint3", "value": 0, "status": false},
        {"id": 9, "name": "关节3屈曲", "action": "屈曲", "joint": "joint3", "value": 2, "status": false},
        
        {"id": 10, "name": "全部停止", "action": "停止", "joint": "all", "value": 0, "status": false}
      ];
    },
    
    // 发送登高车命令
    async sendLiftCommand(buttonId) {
      try {
        const response = await fetch(`/api/lift/button/${buttonId}`, {
          method: 'POST',
        });
        
        const result = await response.json();
        
        if (response.ok) {
          // 更新按钮状态
          this.updateLiftButtonStatus(buttonId, result);
          this.showMessage(`命令已发送: ${this.getLiftButtonName(buttonId)}`, 'success');
        } else {
          this.showMessage(`命令发送失败: ${result.detail || '未知错误'}`, 'error');
        }
      } catch (error) {
        console.error('发送登高车命令时出错:', error);
        this.showMessage(`命令发送失败: ${error.message}`, 'error');
      }
    },
    
    // 更新登高车按钮状态
    updateLiftButtonStatus(buttonId, result) {
      // 重新获取最新的按钮状态
      this.loadLiftButtons();
    },
    
    // 获取登高车按钮名称
    getLiftButtonName(buttonId) {
      const button = this.liftButtons.find(btn => btn.id === buttonId);
      return button ? button.name : `按钮${buttonId}`;
    },
    
    showMessage(text, color = 'success') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    }
  },
  created() {
    console.log('SprayerMonitor component created');
    // 初始化默认登高车按钮
    this.initDefaultLiftButtons();
  },
  mounted() {
    console.log('SprayerMonitor component mounted');
    // 初始检查
    this.checkBackendConnection();
    this.loadLiftButtons();
    
    // 定期检查后端连接
    this.checkBackendTimer = setInterval(() => {
      this.checkBackendConnection();
    }, 5000); // 每5秒检查一次
  },
  beforeUnmount() {
    console.log('SprayerMonitor component unmounting, cleaning up');
    // 清除定时器
    if (this.checkBackendTimer) {
      clearInterval(this.checkBackendTimer);
      this.checkBackendTimer = null;
    }
  }
}
</script>

<style scoped>
.sprayer-monitor-page {
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
  height: 50vh;
  margin-bottom: 20px;
  border-radius: 10px;
  overflow: hidden;
}

.main-layout {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.left-panel {
  flex: 3;
}

.right-panel {
  flex: 1;
  min-width: 320px;
}

.control-card, .info-card {
  background: rgba(18, 18, 18, 0.7);
  border-radius: 10px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  flex: 1;
  min-width: 320px;
  display: flex;
  flex-direction: column;
}

.info-card {
  min-width: 320px;
  height: 100%;
  margin-top: 0;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.status-indicator {
  margin-left: auto;
  font-size: 14px;
  padding: 4px 8px;
  background: rgba(255, 59, 48, 0.2);
  border-radius: 4px;
  color: #ff3b30;
}

.status-indicator.active {
  background: rgba(76, 217, 100, 0.2);
  color: #4cd964;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 16px;
}

.joint-control {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.joint-title {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 5px;
}

.control-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.control-btn {
  flex: 1;
  height: 42px;
  min-width: 120px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  min-width: 80px;
}

.info-value {
  font-size: 14px;
  color: #ff3b30;
}

.info-value.online {
  color: #4cd964;
}

.info-value.offline {
  color: #ff3b30;
}

.mt-4 {
  margin-top: 20px;
}
</style> 