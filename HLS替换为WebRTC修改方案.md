# HLS替换为WebRTC修改方案

## 概述
将机械臂摄像头的视频流协议从HLS (.m3u8) 替换为WebRTC协议，提供更低延迟的实时视频流体验。

**新的WebRTC地址**：
```
http://192.168.43.9/player/webrtc?streamPath=hlsram/live0&isMute=1&auto=1&aspect=0&hasAudio=1&username=admin&auth=f6fdffe48c908deb0f4c3bd36c032e72
```

## 技术对比

### HLS vs WebRTC
| 特性 | HLS | WebRTC |
|------|-----|--------|
| 延迟 | 3-30秒 | < 1秒 |
| 实时性 | 较低 | 极高 |
| 兼容性 | 广泛支持 | 现代浏览器支持 |
| 实现复杂度 | 简单 | 中等 |
| 音频支持 | 支持 | 支持 |

## 修改方案

### 1. 前端修改

#### 1.1 创建WebRTC视频组件
**新文件**: `frontend/src/components/video/WebRtcStream.vue`

**主要功能**：
- 使用WebRTC API连接视频流
- 支持音频/视频控制
- 提供连接状态管理
- 错误处理和重连机制

**技术实现**：
```javascript
// 使用原生WebRTC API或第三方库
// 支持的方案：
// 1. 原生 RTCPeerConnection API
// 2. 使用 simple-peer 库简化WebRTC操作
// 3. 使用专门的WebRTC播放器库
```

#### 1.2 修改机械臂监控页面
**文件**: `frontend/src/views/ArmMonitor.vue`

**修改内容**：
```vue
<!-- 从 -->
<HlsStream 
  @stream-status-change="updateStreamStatus" 
  :debugMode="debugMode"
  :streamUrl="streamUrl"
  ref="hlsStream" 
/>

<!-- 改为 -->
<WebRtcStream 
  @stream-status-change="updateStreamStatus" 
  :debugMode="debugMode"
  :streamUrl="webrtcUrl"
  :audioEnabled="true"
  ref="webrtcStream" 
/>
```

**数据修改**：
```javascript
data() {
  return {
    // 原来的HLS地址
    // streamUrl: '/hlsram/live0/index.m3u8',
    
    // 新的WebRTC地址
    webrtcUrl: 'http://192.168.43.9/player/webrtc?streamPath=hlsram/live0&isMute=1&auto=1&aspect=0&hasAudio=1&username=admin&auth=f6fdffe48c908deb0f4c3bd36c032e72',
    
    // 其他配置...
  }
}
```

#### 1.3 更新前端依赖
**文件**: `frontend/package.json`

**添加WebRTC相关依赖**：
```json
{
  "dependencies": {
    // 现有依赖...
    "simple-peer": "^9.11.1",  // WebRTC库选项1
    // 或者
    "webrtc-adapter": "^8.2.3" // WebRTC适配器
  }
}
```

#### 1.4 修改Vite代理配置
**文件**: `frontend/vite.config.js`

**更新代理配置**：
```javascript
proxy: {
  // 现有代理...
  
  // 更新WebRTC代理
  '/player': {
    target: 'http://192.168.43.9',
    changeOrigin: true,
    secure: false,
    ws: true,  // 支持WebSocket连接
    rewrite: (path) => path
  }
}
```

### 2. 后端修改

#### 2.1 更新机械臂流服务
**文件**: `backend/app/arm_streaming.py`

**修改流地址和检查逻辑**：
```python
class ArmStreamingService:
    def __init__(self, stream_url: str = "http://192.168.43.9/player/webrtc?streamPath=hlsram/live0&isMute=1&auto=1&aspect=0&hasAudio=1&username=admin&auth=f6fdffe48c908deb0f4c3bd36c032e72"):
        # 更新初始化参数...
```

**修改状态检查方法**：
```python
def check_camera_connection(self) -> bool:
    """检查WebRTC流状态"""
    # 由于WebRTC是基于实时连接的，
    # 可以检查WebRTC信令服务器或播放器端点
    try:
        # 检查WebRTC播放器页面是否可访问
        check_url = "http://192.168.43.9/player/"
        response = requests.get(check_url, timeout=self.connection_timeout)
        # 处理响应...
    except Exception as e:
        # 错误处理...
```

#### 2.2 更新状态信息
**修改返回的流信息**：
```python
def get_stream_info(self) -> Dict[str, Any]:
    return {
        "camera_connected": camera_connected,
        "stream_url": self.stream_url,
        "stream_type": "WebRTC",  # 从 "HLS" 改为 "WebRTC"
        "protocol": "Web Real-Time Communication",  # 更新协议描述
        "audio_enabled": True,    # 新增音频支持标识
        "low_latency_enabled": True,
        "timestamp": time.time()
    }
```

### 3. WebRTC实现方案选择

#### 方案A：使用原生WebRTC API
**优点**：无额外依赖，完全控制
**缺点**：实现复杂，需要处理ICE/STUN/TURN
**适用场景**：需要完全自定义的场景

#### 方案B：使用simple-peer库
**优点**：简化WebRTC操作，易于实现
**缺点**：需要信令服务器配合
**适用场景**：快速实现，有信令服务器支持

#### 方案C：使用iframe嵌入播放器
**优点**：实现最简单，无需复杂WebRTC代码
**缺点**：集成度较低，样式控制有限
**适用场景**：快速集成，对自定义要求不高

### 4. 推荐实现方案（方案C - iframe嵌入）

考虑到实现复杂度和快速部署的需求，推荐使用iframe方式：

#### 4.1 WebRtcStream.vue实现
```vue
<template>
  <div class="webrtc-stream">
    <iframe
      v-if="isStreamActive"
      :src="iframeUrl"
      class="webrtc-iframe"
      frameborder="0"
      allow="microphone; camera; autoplay"
      allowfullscreen
    ></iframe>
    
    <!-- 加载和离线状态 -->
    <div v-if="isConnecting" class="connecting-overlay">
      <div class="loader"></div>
      <div class="connecting-text">正在连接 WebRTC 视频流...</div>
    </div>
    
    <div v-if="!isStreamActive && !isConnecting" class="offline-overlay">
      <div class="offline-message">VIDEO SIGNAL OFFLINE</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WebRtcStream',
  props: {
    streamUrl: {
      type: String,
      required: true
    },
    autoConnect: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isStreamActive: false,
      isConnecting: false
    }
  },
  computed: {
    iframeUrl() {
      return this.streamUrl;
    }
  },
  // 组件逻辑...
}
</script>
```

### 5. 修改文件清单

#### 5.1 需要修改的文件
```
frontend/src/
├── components/video/WebRtcStream.vue     # 新建WebRTC组件
├── views/ArmMonitor.vue                  # 修改引用WebRTC组件
├── package.json                          # 可能需要添加依赖
└── vite.config.js                        # 更新代理配置

backend/app/
└── arm_streaming.py                      # 更新流地址和状态检查
```

#### 5.2 可能需要删除的文件
```
frontend/src/components/video/HlsStream.vue  # 如果不再使用HLS
```

### 6. 实施步骤

1. **第一步**：创建WebRtcStream.vue组件（iframe方式）
2. **第二步**：修改ArmMonitor.vue使用新组件
3. **第三步**：更新后端流地址和状态检查
4. **第四步**：更新Vite代理配置
5. **第五步**：测试WebRTC视频流功能
6. **第六步**：优化样式和用户体验

### 7. 注意事项

#### 7.1 浏览器兼容性
- WebRTC需要HTTPS环境（生产环境）
- 确保浏览器支持WebRTC
- 音频权限可能需要用户授权

#### 7.2 网络要求
- WebRTC对网络质量要求较高
- 可能需要STUN/TURN服务器（复杂环境）
- 防火墙配置可能需要调整

#### 7.3 性能考虑
- WebRTC资源占用可能比HLS高
- 需要测试多用户并发性能
- 考虑回退到HLS的方案

### 8. 测试验证

#### 8.1 功能测试
- [ ] WebRTC视频流正常播放
- [ ] 音频输出正常工作
- [ ] 连接状态正确显示
- [ ] 错误处理正常
- [ ] 重连机制有效

#### 8.2 性能测试
- [ ] 延迟测试（应< 1秒）
- [ ] 多用户并发测试
- [ ] 长时间稳定性测试
- [ ] 网络抗干扰能力测试

## 风险评估

### 高风险
- WebRTC实现复杂度较高
- 浏览器兼容性问题
- 网络配置要求

### 中风险
- 性能影响未知
- 音频权限处理
- 错误恢复机制

### 低风险
- UI样式调整
- 配置参数修改

## 建议

**推荐采用iframe嵌入方式实现**，因为：
1. 实现简单快速
2. 利用现有的WebRTC播放器
3. 降低开发和维护成本
4. 易于测试和部署

**是否同意按照此方案进行修改？** 