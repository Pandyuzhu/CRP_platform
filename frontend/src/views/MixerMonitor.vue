<template>
  <div class="mixer-monitor-page">
    <div class="page-content">
      <div class="main-title">UHPC 搅拌仓监控</div>
      
      <div class="video-section">
        <VideoStream @stream-status-change="updateStreamStatus" ref="videoStream" />
      </div>
      
      <div class="control-section">
        <!-- 搅拌机1控制区域 -->
        <div class="control-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-blender</v-icon>
            搅拌机1控制
            <div class="status-indicator active">
              可用
            </div>
          </div>
          <div class="control-buttons">
            <div class="control-row" v-for="(pair, index) in mixer1Buttons" :key="'mixer1-'+index">
              <v-btn
                v-for="button in pair"
                :key="button.id"
                :color="button.action === '启动' ? 'success' : 'error'"
                :variant="button.status ? 'flat' : 'outlined'"
                class="control-btn"
                @click="sendCommand('board1', button.id)"
              >
                <v-icon class="mr-2">{{ button.action === '启动' ? 'mdi-play' : 'mdi-stop' }}</v-icon>
                {{ button.name }}
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- 喷射机控制区域 -->
        <div class="control-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-spray</v-icon>
            喷射机控制
            <div class="status-indicator active">
              可用
            </div>
          </div>
          <div class="control-buttons">
            <div class="control-row">
              <v-btn
                v-for="button in sprayerButtons"
                :key="button.id"
                :color="button.action === '启动' ? 'success' : 'error'"
                :variant="button.status ? 'flat' : 'outlined'"
                class="control-btn"
                @click="sendCommand('board1', button.id)"
              >
                <v-icon class="mr-2">{{ button.action === '启动' ? 'mdi-play' : 'mdi-stop' }}</v-icon>
                {{ button.name }}
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- 搅拌机2控制区域 -->
        <div class="control-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-blender-outline</v-icon>
            搅拌机2控制
            <div class="status-indicator active">
              可用
            </div>
          </div>
          <div class="control-buttons">
            <div class="control-row" v-for="(pair, index) in mixer2Buttons" :key="'mixer2-'+index">
              <v-btn
                v-for="button in pair"
                :key="button.id"
                :color="button.action === '启动' ? 'success' : 'error'"
                :variant="button.status ? 'flat' : 'outlined'"
                class="control-btn"
                @click="sendCommand('board2', button.id)"
              >
                <v-icon class="mr-2">{{ button.action === '启动' ? 'mdi-play' : 'mdi-stop' }}</v-icon>
                {{ button.name }}
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- 末端喷头控制区域 -->
        <div class="control-card">
          <div class="card-title">
            <v-icon color="primary" class="mr-2">mdi-nozzle</v-icon>
            末端喷头控制
            <div class="status-indicator active">
              可用
            </div>
          </div>
          <div class="control-buttons">
            <div class="control-row" v-for="(pair, index) in nozzleButtons" :key="'nozzle-'+index">
              <v-btn
                v-for="button in pair"
                :key="button.id"
                :color="button.action === '启动' ? 'success' : 'error'"
                :variant="button.status ? 'flat' : 'outlined'"
                class="control-btn"
                @click="sendCommand('board2', button.id)"
              >
                <v-icon class="mr-2">{{ button.action === '启动' ? 'mdi-play' : 'mdi-stop' }}</v-icon>
                {{ button.name }}
              </v-btn>
            </div>
          </div>
        </div>
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
              <span class="info-label">摄像头:</span>
              <span class="info-value" :class="{ 'online': isStreamActive, 'offline': !isStreamActive }">
                {{ isStreamActive ? '已连接' : '未连接' }}
              </span>
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
import VideoStream from '../components/video/VideoStream.vue';

export default {
  name: 'MixerMonitor',
  components: {
    VideoStream
  },
  data() {
    return {
      isStreamActive: false,
      isBackendConnected: false,
      checkBackendTimer: null,
      
      // 控制板1上的按钮 (搅拌机1和喷射机)
      board1Buttons: [],
      
      // 控制板2上的按钮 (搅拌机2和末端喷头)
      board2Buttons: [],
      
      // 通知消息
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
    }
  },
  computed: {
    // 将按钮分组为每行两个按钮
    mixer1Buttons() {
      // 获取控制板1上搅拌机相关的按钮
      const mixerButtons = this.board1Buttons.filter(btn => 
        ['搅拌运行', '搅拌停止', '输送启动', '输送停止', '水泵启动', '水泵停止', '水阀启动', '水阀停止'].includes(btn.name)
      );
      
      // 按照启动/停止对分组
      return this.pairButtons(mixerButtons);
    },
    
    sprayerButtons() {
      // 获取控制板1上喷射机相关的按钮
      return this.board1Buttons.filter(btn => 
        ['喷浆启动', '喷浆停止', '喷浆反转'].includes(btn.name)
      );
    },
    
    mixer2Buttons() {
      // 获取控制板2上搅拌机相关的按钮
      const mixerButtons = this.board2Buttons.filter(btn => 
        ['搅拌运行', '搅拌停止', '输送启动', '输送停止', '水泵启动', '水泵停止', '水阀启动', '水阀停止'].includes(btn.name)
      );
      
      // 按照启动/停止对分组
      return this.pairButtons(mixerButtons);
    },
    
    nozzleButtons() {
      // 获取控制板2上末端喷头相关的按钮
      console.log('board2Buttons:', this.board2Buttons);
      const nozzleButtons = this.board2Buttons.filter(btn => 
        ['纤维喷射启动', '纤维喷射停止', '浆料喷射启动', '浆料喷射停止'].includes(btn.name)
      );
      console.log('过滤后的nozzleButtons:', nozzleButtons);
      
      // 按照启动/停止对分组
      return this.pairButtons(nozzleButtons);
    }
  },
  methods: {
    // 将按钮列表按照启动/停止对进行分组
    pairButtons(buttons) {
      const result = [];
      let currentPair = [];
      
      for (let i = 0; i < buttons.length; i++) {
        currentPair.push(buttons[i]);
        
        if (currentPair.length === 2 || i === buttons.length - 1) {
          result.push(currentPair);
          currentPair = [];
        }
      }
      
      return result;
    },
    
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
          // 可以使用后端返回的数据更新其他状态
          console.log('Backend status:', data);
        })
        .catch(error => {
          console.error('Backend connection error:', error);
          this.isBackendConnected = false;
          this.isStreamActive = false;
        });
    },
    
    loadDeviceButtons() {
      // 加载设备按钮数据
      fetch('/api/esp32/status')
        .then(response => {
          if (!response.ok) {
            throw new Error('设备按钮数据获取失败');
          }
          return response.json();
        })
        .then(data => {
          console.log('Device buttons data:', data);
          
          // 更新按钮数据
          if (data.board1) {
            this.board1Buttons = data.board1.buttons || [];
          }
          
          if (data.board2) {
            this.board2Buttons = data.board2.buttons || [];
          }
        })
        .catch(error => {
          console.error('Device buttons data error:', error);
          // 如果没有按钮数据，初始化默认的按钮数据
          this.initDefaultButtons();
        });
    },
    
    // 如果无法从后端获取按钮数据，使用默认的按钮数据
    initDefaultButtons() {
      // 控制板1上的按钮 (搅拌机1和喷射机)
      this.board1Buttons = [
        {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": false},
        {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": false},
        {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": false},
        {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": false},
        {"id": 5, "name": "喷浆启动", "action": "启动", "hex_code": "0x0010", "status": false},
        {"id": 6, "name": "喷浆停止", "action": "停止", "hex_code": "0x0020", "status": false},
        {"id": 7, "name": "水泵启动", "action": "启动", "hex_code": "0x0040", "status": false},
        {"id": 8, "name": "水泵停止", "action": "停止", "hex_code": "0x0080", "status": false},
        {"id": 9, "name": "水阀启动", "action": "启动", "hex_code": "0x0100", "status": false},
        {"id": 10, "name": "水阀停止", "action": "停止", "hex_code": "0x0200", "status": false}
      ];
      
      // 控制板2上的按钮 (搅拌机2和末端喷头)
      this.board2Buttons = [
        {"id": 1, "name": "搅拌运行", "action": "启动", "hex_code": "0x0001", "status": false},
        {"id": 2, "name": "搅拌停止", "action": "停止", "hex_code": "0x0002", "status": false},
        {"id": 3, "name": "输送启动", "action": "启动", "hex_code": "0x0004", "status": false},
        {"id": 4, "name": "输送停止", "action": "停止", "hex_code": "0x0008", "status": false},
        {"id": 5, "name": "水泵启动", "action": "启动", "hex_code": "0x0010", "status": false},
        {"id": 6, "name": "水泵停止", "action": "停止", "hex_code": "0x0020", "status": false},
        {"id": 7, "name": "水阀启动", "action": "启动", "hex_code": "0x0040", "status": false},
        {"id": 8, "name": "水阀停止", "action": "停止", "hex_code": "0x0080", "status": false},
        {"id": 9, "name": "纤维喷射启动", "action": "启动", "hex_code": "0x0100", "status": false},
        {"id": 10, "name": "纤维喷射停止", "action": "停止", "hex_code": "0x0200", "status": false},
        {"id": 11, "name": "浆料喷射启动", "action": "启动", "hex_code": "0x0400", "status": false},
        {"id": 12, "name": "浆料喷射停止", "action": "停止", "hex_code": "0x0800", "status": false}
      ];
    },
    
    async sendCommand(boardId, buttonId) {
      try {
        // 发送命令到ESP32控制板
        const response = await fetch(`/api/esp32/${boardId}/button/${buttonId}`, {
          method: 'POST',
        });
        
        const result = await response.json();
        
        if (response.ok) {
          // 手动更新按钮状态
          this.updateButtonStatus(boardId, buttonId);
          // 显示成功消息
          this.showMessage(`命令已发送: ${this.getButtonName(boardId, buttonId)}`, 'success');
        } else {
          this.showMessage(`命令发送失败: ${result.detail || '未知错误'}`, 'error');
        }
      } catch (error) {
        console.error('发送命令时出错:', error);
        this.showMessage(`命令发送失败: ${error.message}`, 'error');
      }
    },
    
    // 手动更新按钮状态
    updateButtonStatus(boardId, buttonId) {
      const buttons = boardId === 'board1' ? this.board1Buttons : this.board2Buttons;
      const button = buttons.find(btn => btn.id === buttonId);
      
      if (!button) return;
      
      // 更新按钮状态
      if (button.action === '启动') {
        button.status = true;
        // 将对应的停止按钮状态设为false
        if (buttonId % 2 === 1) { // 奇数ID是启动按钮
          const stopButton = buttons.find(btn => btn.id === buttonId + 1);
          if (stopButton) stopButton.status = false;
        }
      } else {
        button.status = false;
        // 将对应的启动按钮状态设为false
        if (buttonId % 2 === 0) { // 偶数ID是停止按钮
          const startButton = buttons.find(btn => btn.id === buttonId - 1);
          if (startButton) startButton.status = false;
        }
      }
    },
    
    // 获取按钮名称
    getButtonName(boardId, buttonId) {
      const buttons = boardId === 'board1' ? this.board1Buttons : this.board2Buttons;
      const button = buttons.find(btn => btn.id === buttonId);
      return button ? button.name : `按钮${buttonId}`;
    },
    
    showMessage(text, color = 'success') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
    
    // 确保末端喷头按钮名称正确
    fixNozzleButtonNames() {
      const nozzleButtonNames = {
        9: "纤维喷射启动",
        10: "纤维喷射停止",
        11: "浆料喷射启动",
        12: "浆料喷射停止"
      };
      
      // 更新末端喷头按钮名称
      this.board2Buttons.forEach(button => {
        if (nozzleButtonNames[button.id]) {
          console.log(`更新按钮名称: ${button.name} -> ${nozzleButtonNames[button.id]}`);
          button.name = nozzleButtonNames[button.id];
        }
      });
    }
  },
  created() {
    console.log('MixerMonitor component created');
    // 确保初始化默认按钮数据
    this.initDefaultButtons();
    console.log('初始化默认按钮: ', this.board2Buttons);
    
    // 确保末端喷头按钮名称正确
    this.fixNozzleButtonNames();
  },
  mounted() {
    console.log('MixerMonitor component mounted');
    // 初始检查
    this.checkBackendConnection();
    this.loadDeviceButtons();
    
    // 定期检查后端连接
    this.checkBackendTimer = setInterval(() => {
      this.checkBackendConnection();
    }, 5000); // 每5秒检查一次
  },
  beforeUnmount() {
    console.log('MixerMonitor component unmounting, cleaning up');
    // 清除定时器
    if (this.checkBackendTimer) {
      clearInterval(this.checkBackendTimer);
      this.checkBackendTimer = null;
    }
  }
}
</script>

<style scoped>
.mixer-monitor-page {
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
}

.video-section {
  width: 100%;
  height: 50vh;
  margin-bottom: 20px;
  border-radius: 10px;
  overflow: hidden;
}

.control-section {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  margin-bottom: 20px;
}

.control-card, .info-card {
  background: rgba(18, 18, 18, 0.7);
  border-radius: 10px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  min-width: 300px;
  flex: 1;
  max-width: 500px;
  display: flex;
  flex-direction: column;
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
  gap: 10px;
  margin-top: 16px;
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

.info-section {
  display: flex;
  gap: 20px;
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
    height: 40vh;
  }
  
  .info-content {
    grid-template-columns: 1fr;
  }
}
</style> 