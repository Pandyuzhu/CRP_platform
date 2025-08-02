<template>
  <div class="nav-bar">
    <div class="nav-container">
      <div class="logo">
        <v-icon color="primary" size="large">mdi-shield-account</v-icon>
        <span class="logo-text">机器人建造平台（CRP）</span>
      </div>
      <div class="nav-links">
        <router-link 
          :to="{ name: 'mixer' }" 
          :class="{ 'active': currentRoute === 'mixer' }"
          class="nav-link"
        >
          <v-icon size="small" class="mr-1">mdi-rotate-3d</v-icon>
          搅拌仓监控
        </router-link>
        <router-link 
          :to="{ name: 'spray' }" 
          :class="{ 'active': currentRoute === 'spray' }"
          class="nav-link"
        >
          <v-icon size="small" class="mr-1">mdi-camera</v-icon>
          喷射监控
        </router-link>
        <router-link 
          :to="{ name: 'rtk' }" 
          :class="{ 'active': currentRoute === 'rtk' }"
          class="nav-link"
        >
          <v-icon size="small" class="mr-1">mdi-map-marker-path</v-icon>
          RTK定位监控
        </router-link>
        <router-link 
          :to="{ name: 'arm' }" 
          :class="{ 'active': currentRoute === 'arm' }"
          class="nav-link"
        >
          <v-icon size="small" class="mr-1">mdi-robot-industrial</v-icon>
          机械臂监控
        </router-link>
      </div>
      <div class="system-status">
        <div class="status-indicator" :class="{ 'online': isSystemOnline }"></div>
        <span>{{ isSystemOnline ? '系统在线' : '系统离线' }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NavBar',
  data() {
    return {
      isSystemOnline: true
    }
  },
  computed: {
    currentRoute() {
      return this.$route.name;
    }
  }
}
</script>

<style scoped>
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  z-index: 100;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
}

.logo-text {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 500;
  font-size: 18px;
  color: #fff;
  margin-left: 10px;
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 30px;
}

.nav-link {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  text-decoration: none;
  padding: 5px 0;
  position: relative;
  transition: color 0.2s ease;
  display: flex;
  align-items: center;
}

.nav-link:hover {
  color: rgba(255, 255, 255, 1);
}

.nav-link.active {
  color: #fff;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #3EDBF0, #04D9FF);
}

.system-status {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(255, 0, 0, 0.7);
  margin-right: 8px;
}

.status-indicator.online {
  background-color: rgba(0, 255, 0, 0.7);
}
</style> 