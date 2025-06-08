import { createRouter, createWebHistory } from 'vue-router'
import MixerMonitor from '../views/MixerMonitor.vue'
import SprayerMonitor from '../views/SprayerMonitor.vue'
import VideoMonitor from '../views/VideoMonitor.vue'
// import SprayMonitor from '../views/SprayMonitor.vue'
const routes = [
  // 默认路由重定向到搅拌监控
  { 
    path: '/', 
    redirect: '/mixer' 
  },
  
  // 搅拌仓监控
  { 
    path: '/mixer', 
    component: MixerMonitor, 
    name: 'mixer' 
  },
  
  // 喷射监控
  { 
    path: '/spray', 
    component: SprayerMonitor, 
    name: 'spray' 
  },
  
  // 保留旧的视频路由以向后兼容
  { 
    path: '/video', 
    component: VideoMonitor, 
    name: 'video' 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 