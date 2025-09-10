import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/admin-api': { target: 'http://localhost:8080', changeOrigin: true },
    },
    // WSL/파일감지 이슈시 주석 해제
    // watch: { usePolling: true }
  },
})
