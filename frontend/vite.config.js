import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      },
      // 添加WebRTC播放器代理，解决CORS问题
      '/player': {
        target: 'http://192.168.0.51',
        changeOrigin: true,
        secure: false,
        ws: true,  // 支持WebSocket连接
        rewrite: (path) => path
      },
      // 保留HLS代理以备其他用途
      '/hlsram': {
        target: 'http://192.168.0.51:80',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  }
}); 