<template>
  <div class="hls-stream">
    <!-- HLS Video Stream - 始终渲染，通过CSS控制显示 -->
    <video 
      ref="videoElement" 
      class="video-feed" 
      :style="{ display: isStreamActive ? 'block' : 'none' }"
      autoplay 
      muted 
      playsinline
      controls
      crossorigin="anonymous"
    ></video>
    
    <!-- Loading State -->
    <div v-if="isConnecting" class="connecting-overlay">
      <div class="loader"></div>
      <div class="connecting-text">正在连接 HLS 视频流...</div>
    </div>
    
    <!-- Offline State -->
    <div v-if="!isStreamActive && !isConnecting" class="offline-overlay">
      <div class="offline-message">VIDEO SIGNAL OFFLINE</div>
      <div class="offline-details">{{ lastError || '等待视频流连接' }}</div>
    </div>
    
    <!-- Debug Panel -->
    <div v-if="debugMode" class="debug-panel">
      <div class="debug-title">调试信息</div>
      <div class="debug-item">HLS支持: {{ hlsSupported ? '✓' : '✗' }}</div>
      <div class="debug-item">原生HLS支持: {{ nativeHlsSupported ? '✓' : '✗' }}</div>
      <div class="debug-item">当前状态: {{ currentStatus }}</div>
      <div class="debug-item">流地址: {{ streamUrl }}</div>
      <div class="debug-item">重连次数: {{ reconnectAttempts }}/{{ maxReconnectAttempts }}</div>
      <div class="debug-item" v-if="lastError">错误信息: {{ lastError }}</div>
    </div>
  </div>
</template>

<script>
import Hls from 'hls.js';

export default {
  name: 'HlsStream',
  emits: ['stream-status-change'],
  props: {
    autoConnect: {
      type: Boolean,
      default: true
    },
    streamUrl: {
      type: String,
      default: '/hlsram/live0/index.m3u8'  // 使用代理路径
    },
    debugMode: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isStreamActive: false,
      isConnecting: false,
      hls: null,
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimer: null,
      statusCheckTimer: null,
      latencyCheckTimer: null,  // 新增：延迟检查定时器
      lastErrorTime: 0,
      _hasInitialized: false,
      lastError: '',
      currentStatus: '未初始化',
      hlsSupported: false,
      nativeHlsSupported: false
    }
  },
  watch: {
    isStreamActive(newValue) {
      this.$emit('stream-status-change', newValue);
    }
  },
  methods: {
    async startStream() {
      // 防止重复连接
      if (this.isConnecting || this.isStreamActive || this.hls) {
        console.log('HLS流已连接或正在连接中，不重复连接');
        return;
      }
      
      this.isConnecting = true;
      this.currentStatus = '正在连接';
      this.lastError = '';
      
      // 检查浏览器支持情况
      this.hlsSupported = Hls.isSupported();
      this.nativeHlsSupported = this.checkNativeHlsSupport();
      
      if (this.debugMode) {
        console.log('HLS支持检查:', {
          hlsJsSupported: this.hlsSupported,
          nativeSupported: this.nativeHlsSupported,
          streamUrl: this.streamUrl
        });
      }
      
      // 检查流可用性
      const streamAvailable = await this.checkStreamAvailability();
      if (!streamAvailable && this.debugMode) {
        console.warn('流地址预检查失败，但继续尝试连接');
      }
      
      try {
        const video = this.$refs.videoElement;
        if (!video) {
          const error = 'Video element not found';
          console.error(error);
          this.lastError = error;
          this.handleConnectionFailure();
          return;
        }

        if (Hls.isSupported()) {
          // 使用hls.js，先尝试标准配置
          const hlsConfig = {
            debug: this.debugMode,
            enableWorker: true,
            autoStartLoad: true,
            startPosition: -1,
            capLevelToPlayerSize: true,
            
            // === 低延迟优化配置 ===
            // 减少缓冲时间
            maxBufferLength: 3,           // 最大缓冲3秒（原30秒）
            maxMaxBufferLength: 10,       // 最大缓冲10秒（原600秒）
            maxBufferSize: 10 * 1000 * 1000,  // 10MB缓冲（原60MB）
            maxBufferHole: 0.1,           // 减少缓冲空洞容忍度
            
            // 快速开始播放
            lowLatencyMode: true,         // 启用低延迟模式
            backBufferLength: 2,          // 后向缓冲2秒
            liveSyncDurationCount: 1,     // 实时同步片段数量
            liveMaxLatencyDurationCount: 3, // 最大延迟片段数量
            
            // 快速加载和切换
            maxLoadingDelay: 1,           // 最大加载延迟1秒
            maxFragLookUpTolerance: 0.1,  // 片段查找容忍度
            highBufferWatchdogPeriod: 1,  // 高缓冲监控周期
            
            // 播放策略优化
            manifestLoadingTimeOut: 5000,     // 清单加载超时5秒
            manifestLoadingMaxRetry: 2,       // 清单加载最大重试2次
            fragLoadingTimeOut: 10000,        // 片段加载超时10秒
            fragLoadingMaxRetry: 3            // 片段加载最大重试3次
          };
          
          this.hls = new Hls(hlsConfig);
          
          this.hls.loadSource(this.streamUrl);
          this.hls.attachMedia(video);
          
          // HLS事件处理
          this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('HLS manifest parsed, starting playback');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.currentStatus = '清单已解析，开始播放';
            
            // === 新增：跳转到最新位置 ===
            const levels = this.hls.levels;
            if (levels && levels.length > 0) {
              // 跳转到最新的可用位置（减少延迟）
              const duration = this.hls.media.duration;
              if (duration && duration > 10) {
                // 如果总时长大于10秒，跳转到最后10秒的位置
                this.hls.media.currentTime = Math.max(0, duration - 10);
              }
            }
            
            video.play().then(() => {
              this.isStreamActive = true;
              this.currentStatus = '播放中';
              console.log('HLS stream started successfully');
              
              // === 新增：监控和调整播放位置 ===
              this.startLatencyOptimization();
            }).catch(error => {
              const errorMsg = `播放启动失败: ${error.message}`;
              console.error(errorMsg, error);
              this.lastError = errorMsg;
              this.currentStatus = '播放失败';
              this.handleConnectionFailure();
            });
          });
          
          this.hls.on(Hls.Events.ERROR, (event, data) => {
            const errorInfo = {
              type: data.type,
              details: data.details,
              fatal: data.fatal,
              url: this.streamUrl,
              response: data.response
            };
            
            console.error('HLS详细错误信息:', errorInfo);
            
            if (data.fatal) {
              this.handleFatalError(data);
            } else {
              this.handleNonFatalError(data);
            }
          });
          
          // 视频事件处理
          video.addEventListener('loadstart', () => {
            console.log('Video load started');
          });
          
          video.addEventListener('canplay', () => {
            console.log('Video can start playing');
          });
          
          video.addEventListener('error', (error) => {
            console.error('Video element error:', error);
            this.handleConnectionFailure();
          });
          
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // 原生HLS支持（Safari）
          video.src = this.streamUrl;
          
          video.addEventListener('loadedmetadata', () => {
            console.log('Native HLS loaded');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            video.play().then(() => {
              this.isStreamActive = true;
              console.log('Native HLS stream started successfully');
            }).catch(error => {
              console.error('Error starting native HLS playback:', error);
              this.handleConnectionFailure();
            });
          });
          
          video.addEventListener('error', (error) => {
            console.error('Native HLS error:', error);
            this.handleConnectionFailure();
          });
          
        } else {
          console.error('HLS is not supported in this browser');
          this.handleConnectionFailure();
        }
        
      } catch (error) {
        console.error('Error setting up HLS stream:', error);
        this.handleConnectionFailure();
      }
    },
    
    stopStream() {
      console.log('停止HLS视频流');
      
      // 停止延迟优化监控
      this.stopLatencyOptimization();
      
      if (this.hls) {
        this.hls.destroy();
        this.hls = null;
      }
      
      const video = this.$refs.videoElement;
      if (video) {
        video.pause();
        video.src = '';
        video.load();
      }
      
      this.isStreamActive = false;
      this.isConnecting = false;
      this.clearTimers();
    },
    
    handleConnectionFailure() {
      this.isStreamActive = false;
      this.isConnecting = false;
      this.currentStatus = '连接失败';
      
      if (this.hls) {
        this.hls.destroy();
        this.hls = null;
      }
      
      // 自动重连逻辑
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect();
      } else {
        this.currentStatus = '重连次数已达上限';
        this.lastError = '已达到最大重连次数，请检查网络连接和流地址';
        console.log('Maximum reconnect attempts reached');
      }
    },
    
    handleNetworkError() {
      const now = Date.now();
      if (now - this.lastErrorTime > 2000) { // 防抖：2秒内不重复处理
        this.lastErrorTime = now;
        
        if (this.hls) {
          setTimeout(() => {
            if (this.hls) {
              this.hls.startLoad();
            }
          }, 1000);
        }
      }
    },
    
    attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        
        this.clearTimers();
        this.reconnectTimer = setTimeout(() => {
          console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
          this.startStream();
        }, Math.min(2000 * this.reconnectAttempts, 10000)); // 指数退避，最大10秒
      }
    },
    
    clearTimers() {
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      if (this.statusCheckTimer) {
        clearInterval(this.statusCheckTimer);
        this.statusCheckTimer = null;
      }
      // 新增：清理延迟检查定时器
      if (this.latencyCheckTimer) {
        clearInterval(this.latencyCheckTimer);
        this.latencyCheckTimer = null;
      }
    },
    
    // 确保在组件失活时停止流
    deactivateComponent() {
      console.log('HlsStream组件被缓存，停止连接');
      this.stopStream();
    },
    
    // 组件重新激活时
    activateComponent() {
      console.log('HlsStream组件被激活，重新检查连接状态');
      if (this.autoConnect) {
        this.startStream();
      }
    },
    
    // 检查原生HLS支持
    checkNativeHlsSupport() {
      const video = document.createElement('video');
      return video.canPlayType('application/vnd.apple.mpegurl') !== '';
    },
    
    // 检查流可用性
    async checkStreamAvailability() {
      try {
        const response = await fetch(this.streamUrl, { 
          method: 'HEAD',
          mode: 'no-cors'
        });
        return true;
      } catch (error) {
        console.error('流地址检查失败:', error);
        return false;
      }
    },
    
    // === 新增：延迟优化相关方法 ===
    // 启动延迟优化监控
    startLatencyOptimization() {
      // 每5秒检查一次播放延迟
      this.latencyCheckTimer = setInterval(() => {
        this.checkAndAdjustLatency();
      }, 5000);
    },
    
    // 检查并调整播放延迟
    checkAndAdjustLatency() {
      if (!this.hls || !this.hls.media) return;
      
      const video = this.hls.media;
      const currentTime = video.currentTime;
      const duration = video.duration;
      
      // 如果延迟超过15秒，跳转到更接近实时的位置
      if (duration && (duration - currentTime) > 15) {
        const targetTime = Math.max(0, duration - 5);
        console.log(`延迟过高，从 ${currentTime.toFixed(1)}s 跳转到 ${targetTime.toFixed(1)}s`);
        video.currentTime = targetTime;
      }
    },
    
    // 停止延迟优化监控
    stopLatencyOptimization() {
      if (this.latencyCheckTimer) {
        clearInterval(this.latencyCheckTimer);
        this.latencyCheckTimer = null;
      }
    },
    
    // 处理致命错误
    handleFatalError(data) {
      const errorMsg = `致命错误 - ${data.type}: ${data.details}`;
      this.lastError = errorMsg;
      this.currentStatus = '致命错误';
      
      switch (data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
          console.log('致命网络错误，尝试恢复');
          this.currentStatus = '网络错误，重试中';
          this.handleNetworkError();
          break;
        case Hls.ErrorTypes.MEDIA_ERROR:
          console.log('致命媒体错误，尝试恢复');
          this.currentStatus = '媒体错误，重试中';
          if (this.hls) {
            this.hls.recoverMediaError();
          }
          break;
        default:
          console.log('无法恢复的致命错误');
          this.currentStatus = '无法恢复的错误';
          this.handleConnectionFailure();
          break;
      }
    },
    
    // 处理非致命错误
    handleNonFatalError(data) {
      const errorMsg = `非致命错误 - ${data.type}: ${data.details}`;
      console.warn(errorMsg);
      if (this.debugMode) {
        this.lastError = errorMsg;
      }
    }
  },
  mounted() {
    console.log('HlsStream component mounted');
    
    // 如果autoConnect为true，延迟启动流
    if (this.autoConnect && !this._hasInitialized) {
      setTimeout(() => {
        this.startStream();
      }, 500);
      
      this._hasInitialized = true;
    }
  },
  beforeUnmount() {
    console.log('HlsStream component unmounting, cleaning up');
    this.stopStream();
  },
  activated() {
    console.log('HlsStream component activated');
    this.activateComponent();
  },
  deactivated() {
    console.log('HlsStream component deactivated');
    this.deactivateComponent();
  }
}
</script>

<style scoped>
.hls-stream {
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
  margin-bottom: 10px;
}

.offline-details {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  text-align: center;
}

.connecting-text {
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  margin-top: 15px;
  text-align: center;
}

.debug-panel {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.8);
  padding: 15px;
  border-radius: 8px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 12px;
  color: #fff;
  max-width: 300px;
  z-index: 10;
}

.debug-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #4cd964;
  border-bottom: 1px solid rgba(255,255,255,0.2);
  padding-bottom: 5px;
}

.debug-item {
  margin-bottom: 5px;
  word-break: break-all;
}
</style> 