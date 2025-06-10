/**
 * 前端全局配置
 */

// API 基础URL
export const apiBaseUrl = 'http://localhost:8000';

// 其他全局配置
export const config = {
  // 应用名称
  appName: '智能建筑平台',
  
  // 刷新间隔（毫秒）
  refreshInterval: 1000,
  
  // 默认坐标原点
  defaultOrigin: {
    e: 0,
    n: 0,
    u: 0
  },
  
  // 3D可视化配置
  visualization: {
    gridSize: 10,
    axisLength: 5,
    baseStationColor: 0xff0000,
    deviceColor: 0x0066ff
  }
};

export default {
  apiBaseUrl,
  ...config
}; 